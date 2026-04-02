"""
GameManager - Singleton pattern for managing real-time Battle Royale game sessions.
Handles WebSocket connections, game state, scoring, round statistics,
and league assignment at the end of the game.
"""

import asyncio
import json
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fastapi import WebSocket

# Grace period in seconds — answers arriving within this window after timer
# expires are still accepted (compensates for network latency).
ANSWER_GRACE_PERIOD = 2.5

# Minimum players required for league split
MIN_PLAYERS_FOR_LEAGUES = 4

# Minimum average score (per question) to qualify for champions league
# e.g., 4 means at least 40% of max possible points per question
MIN_SCORE_FOR_CHAMPIONS = 4

# Seconds to show results before loading next question
RESULTS_DISPLAY_TIME = 6
LOADING_DISPLAY_TIME = 2


@dataclass
class Player:
    nickname: str
    websocket: WebSocket
    score: int = 0
    is_alive: bool = True
    current_answer: int | None = None
    answer_time: float | None = None
    streak: int = 0
    correct_count: int = 0
    total_answered: int = 0
    league: str = ""  # "", "champions", "challengers"


@dataclass
class GameRoom:
    pin: str
    course_id: int
    professor_id: int
    professor_ws: WebSocket | None = None
    players: dict[str, Player] = field(default_factory=dict)
    questions: list[dict] = field(default_factory=list)
    current_question_index: int = -1
    status: str = "waiting"  # waiting, playing, round_active, round_ended, loading_next, finished
    time_per_question: int = 30
    round_start_time: float = 0
    # Mapping from shuffled index -> original index for current question
    shuffle_map: list[int] = field(default_factory=list)
    # The original correct_index for the current question (before shuffle)
    original_correct_index: int = -1
    # Round history for statistics
    round_history: list[dict] = field(default_factory=list)


class GameManager:
    """Singleton game manager for all active game sessions."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._rooms: dict[str, GameRoom] = {}
        return cls._instance

    @staticmethod
    def generate_pin() -> str:
        return ''.join(random.choices(string.digits, k=6))

    def create_room(self, course_id: int, professor_id: int, questions: list[dict],
                    time_per_question: int = 30) -> str:
        pin = self.generate_pin()
        while pin in self._rooms:
            pin = self.generate_pin()

        self._rooms[pin] = GameRoom(
            pin=pin,
            course_id=course_id,
            professor_id=professor_id,
            questions=questions,
            time_per_question=time_per_question,
        )
        return pin

    def get_room(self, pin: str) -> GameRoom | None:
        return self._rooms.get(pin)

    def remove_room(self, pin: str):
        self._rooms.pop(pin, None)

    async def connect_professor(self, pin: str, ws: WebSocket):
        room = self.get_room(pin)
        if not room:
            return
        room.professor_ws = ws
        await ws.send_json({
            "type": "room_created",
            "pin": pin,
            "num_questions": len(room.questions),
        })

    async def connect_player(self, pin: str, nickname: str, ws: WebSocket) -> bool:
        room = self.get_room(pin)
        if not room or room.status != "waiting":
            await ws.send_json({"type": "error", "message": "Sesiunea nu este disponibila"})
            return False

        if nickname in room.players:
            await ws.send_json({"type": "error", "message": "Nickname-ul este deja folosit"})
            return False

        room.players[nickname] = Player(nickname=nickname, websocket=ws)

        await ws.send_json({
            "type": "joined",
            "nickname": nickname,
            "players_count": len(room.players),
        })

        await self._broadcast_player_list(room)
        return True

    async def disconnect_player(self, pin: str, nickname: str):
        room = self.get_room(pin)
        if not room:
            return
        if nickname in room.players:
            del room.players[nickname]
            await self._broadcast_player_list(room)

    async def start_game(self, pin: str):
        room = self.get_room(pin)
        if not room or room.status != "waiting":
            return

        room.status = "playing"
        room.current_question_index = -1

        await self._broadcast_all(room, {
            "type": "game_started",
            "total_questions": len(room.questions),
            "time_per_question": room.time_per_question,
        })

        # Start first question after brief delay
        await asyncio.sleep(3)
        await self._next_question(room)

    async def _next_question(self, room: GameRoom):
        room.current_question_index += 1

        if room.current_question_index >= len(room.questions):
            await self._end_game(room)
            return

        q = room.questions[room.current_question_index]

        room.status = "round_active"
        room.round_start_time = time.time()

        # Reset answers
        for p in room.players.values():
            p.current_answer = None
            p.answer_time = None

        # --- Shuffle options so correct answer is in a random position ---
        original_options = q["options"]
        original_correct = q["correct_index"]
        room.original_correct_index = original_correct

        indices = list(range(len(original_options)))
        random.shuffle(indices)
        room.shuffle_map = indices

        shuffled_options = [original_options[i] for i in indices]
        shuffled_correct_index = indices.index(original_correct)

        # Determine phase label
        total = len(room.questions)
        idx = room.current_question_index
        if idx < 3:
            phase = "Incalzire"
        elif idx < total - 3:
            phase = "Competitie"
        else:
            phase = "Runda Finala"

        # Send question to all players (WITHOUT correct answer!)
        question_data = {
            "type": "question",
            "index": room.current_question_index,
            "total": total,
            "question_text": q["question_text"],
            "options": shuffled_options,
            "difficulty": q.get("difficulty", "medium"),
            "time_limit": room.time_per_question,
            "alive_count": len(room.players),
            "phase": phase,
        }

        for player in room.players.values():
            try:
                await player.websocket.send_json(question_data)
            except Exception:
                pass

        # Send to professor with correct answer marked
        if room.professor_ws:
            try:
                await room.professor_ws.send_json({
                    **question_data,
                    "correct_index": shuffled_correct_index,
                })
            except Exception:
                pass

        # Start timer
        await asyncio.sleep(room.time_per_question + ANSWER_GRACE_PERIOD)
        if room.status == "round_active":
            await self._end_round(room)

    async def submit_answer(self, pin: str, nickname: str, answer: int):
        room = self.get_room(pin)
        if not room or room.status != "round_active":
            return

        player = room.players.get(nickname)
        if not player or player.current_answer is not None:
            return

        elapsed = time.time() - room.round_start_time
        if elapsed > room.time_per_question + ANSWER_GRACE_PERIOD:
            return

        player.current_answer = answer
        player.answer_time = min(elapsed, float(room.time_per_question))
        player.total_answered += 1

        # Notify the player that answer was received
        try:
            await player.websocket.send_json({
                "type": "answer_confirmed",
                "selected": answer,
            })
        except Exception:
            pass

        # Check if all players have answered
        all_answered = all(p.current_answer is not None for p in room.players.values())

        if all_answered:
            await self._end_round(room)

    async def _end_round(self, room: GameRoom):
        if room.status != "round_active":
            return

        room.status = "round_ended"
        q = room.questions[room.current_question_index]
        correct = room.shuffle_map.index(room.original_correct_index) if room.shuffle_map else q["correct_index"]

        # --- Compute round statistics ---
        total_players = len(room.players)
        correct_count = 0
        wrong_count = 0
        timeout_count = 0
        answer_times = []
        fastest_player = None
        fastest_time = float('inf')

        results = {}
        for nickname, player in room.players.items():
            answered_correctly = player.current_answer == correct

            if player.current_answer is None:
                # Didn't answer in time - no points, no elimination
                timeout_count += 1
                player.streak = 0
                results[nickname] = {"status": "timeout", "score": player.score, "points_earned": 0}
            elif answered_correctly:
                correct_count += 1
                player.correct_count += 1
                # Score: base points + speed bonus
                time_bonus = max(0, int((room.time_per_question - (player.answer_time or room.time_per_question)) * 10))
                points = 100 + time_bonus
                player.score += points
                player.streak += 1
                streak_bonus = 0
                if player.streak >= 3:
                    streak_bonus = 50
                    player.score += streak_bonus
                    points += streak_bonus
                results[nickname] = {
                    "status": "correct",
                    "score": player.score,
                    "points_earned": points,
                    "streak": player.streak,
                    "answer_time": round(player.answer_time or 0, 1),
                }
                if player.answer_time and player.answer_time < fastest_time:
                    fastest_time = player.answer_time
                    fastest_player = nickname
                answer_times.append(player.answer_time or room.time_per_question)
            else:
                wrong_count += 1
                player.streak = 0
                results[nickname] = {"status": "wrong", "score": player.score, "points_earned": 0}
                if player.answer_time:
                    answer_times.append(player.answer_time)

        # Build statistics
        accuracy_pct = round((correct_count / total_players * 100)) if total_players > 0 else 0
        avg_time = round(sum(answer_times) / len(answer_times), 1) if answer_times else 0

        round_stats = {
            "total_players": total_players,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "timeout_count": timeout_count,
            "accuracy_pct": accuracy_pct,
            "avg_answer_time": avg_time,
            "fastest_player": fastest_player,
            "fastest_time": round(fastest_time, 1) if fastest_player else None,
        }

        # Save round history
        room.round_history.append({
            "question_index": room.current_question_index,
            "stats": round_stats,
        })

        # Get shuffled options for showing correct answer
        shuffled_options = [q["options"][i] for i in room.shuffle_map] if room.shuffle_map else q["options"]
        correct_answer_text = shuffled_options[correct] if correct < len(shuffled_options) else ""

        round_result = {
            "type": "round_result",
            "question_index": room.current_question_index,
            "correct_index": correct,
            "correct_answer_text": correct_answer_text,
            "explanation": q.get("explanation", ""),
            "alive_count": total_players,
            "leaderboard": self._get_leaderboard(room),
            "round_stats": round_stats,
            "options": shuffled_options,
            "is_last_question": room.current_question_index >= len(room.questions) - 1,
        }

        # Send personalized results to each player
        for nickname, player in room.players.items():
            try:
                personal_result = {
                    **round_result,
                    "your_result": results.get(nickname, {}),
                    "your_answer": player.current_answer,
                    "your_score": player.score,
                    "your_accuracy": round(player.correct_count / max(player.total_answered, 1) * 100),
                    "your_streak": player.streak,
                }
                await player.websocket.send_json(personal_result)
            except Exception:
                pass

        # Send to professor
        if room.professor_ws:
            try:
                await room.professor_ws.send_json({
                    **round_result,
                    "all_results": results,
                })
            except Exception:
                pass

        # Wait for players to see results
        await asyncio.sleep(RESULTS_DISPLAY_TIME)

        # If more questions remain, show loading transition
        if room.current_question_index < len(room.questions) - 1:
            room.status = "loading_next"
            await self._broadcast_all(room, {
                "type": "loading_next",
                "next_index": room.current_question_index + 1,
                "total": len(room.questions),
                "message": "Pregateste-te pentru urmatoarea intrebare...",
            })
            await asyncio.sleep(LOADING_DISPLAY_TIME)
            await self._next_question(room)
        else:
            await self._end_game(room)

    async def _end_game(self, room: GameRoom):
        room.status = "finished"
        leaderboard = self._get_leaderboard(room)
        total_players = len(room.players)

        # --- League assignment ---
        leagues = {"champions": [], "challengers": []}

        if total_players >= MIN_PLAYERS_FOR_LEAGUES:
            total_rounds = room.current_question_index + 1
            min_total_score = MIN_SCORE_FOR_CHAMPIONS * total_rounds

            # Sort by score desc, accuracy desc, speed asc (same as leaderboard)
            sorted_players = sorted(
                room.players.values(),
                key=lambda p: (
                    -p.score,
                    -(p.correct_count / max(p.total_answered, 1)),
                    p.answer_time if p.answer_time is not None else 999,
                ),
            )
            mid = total_players // 2

            for i, player in enumerate(sorted_players):
                # Top half AND meets minimum score -> champions
                if i < mid and player.score >= min_total_score:
                    player.league = "champions"
                    leagues["champions"].append(player.nickname)
                else:
                    player.league = "challengers"
                    leagues["challengers"].append(player.nickname)

            # Update leaderboard with league info
            leaderboard = self._get_leaderboard(room)

        winner = leaderboard[0]["nickname"] if leaderboard else "Nimeni"

        # Final statistics
        total_rounds = room.current_question_index + 1
        game_stats = {
            "total_rounds": total_rounds,
            "total_players": total_players,
        }

        end_data = {
            "type": "game_over",
            "winner": winner,
            "leaderboard": leaderboard,
            "total_rounds": total_rounds,
            "game_stats": game_stats,
            "has_leagues": total_players >= MIN_PLAYERS_FOR_LEAGUES,
            "leagues": leagues,
        }

        # Send personalized game over to each player
        for nickname, player in room.players.items():
            try:
                personal_end = {
                    **end_data,
                    "your_league": player.league,
                    "your_score": player.score,
                    "your_accuracy": round(player.correct_count / max(player.total_answered, 1) * 100),
                }
                await player.websocket.send_json(personal_end)
            except Exception:
                pass

        # Send to professor
        if room.professor_ws:
            try:
                await room.professor_ws.send_json(end_data)
            except Exception:
                pass

        # --- Save results to database ---
        await self._save_results_to_db(room)

    async def _save_results_to_db(self, room: GameRoom):
        """Persist final game results into game_results and update game_sessions."""
        try:
            from models.database import get_db
            db = await get_db()

            cursor = await db.execute(
                "SELECT id FROM game_sessions WHERE pin_code = ?", (room.pin,)
            )
            session_row = await cursor.fetchone()
            if not session_row:
                await db.close()
                return

            session_id = session_row["id"]
            finished_at = datetime.now(timezone.utc).isoformat()

            await db.execute(
                "UPDATE game_sessions SET status = 'finished' WHERE id = ?",
                (session_id,),
            )

            for player in room.players.values():
                await db.execute(
                    """INSERT INTO game_results
                       (session_id, player_name, user_id, score, is_alive, eliminated_at_round, finished_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session_id,
                        player.nickname,
                        None,
                        player.score,
                        1,  # everyone is alive (no elimination)
                        None,
                        finished_at,
                    ),
                )

            await db.commit()
            await db.close()
        except Exception as e:
            print(f"Error saving game results: {e}")

    def _get_leaderboard(self, room: GameRoom) -> list[dict]:
        # Tiebreaker: score desc, then accuracy desc, then avg answer time asc
        players = sorted(
            room.players.values(),
            key=lambda p: (
                -p.score,
                -(p.correct_count / max(p.total_answered, 1)),
                p.answer_time if p.answer_time is not None else 999,
            ),
        )
        return [
            {
                "rank": i + 1,
                "nickname": p.nickname,
                "score": p.score,
                "is_alive": True,
                "streak": p.streak,
                "correct_count": p.correct_count,
                "total_answered": p.total_answered,
                "accuracy": round(p.correct_count / max(p.total_answered, 1) * 100),
                "league": p.league,
            }
            for i, p in enumerate(players)
        ]

    async def _broadcast_player_list(self, room: GameRoom):
        player_list = {
            "type": "player_list",
            "players": [
                {"nickname": p.nickname}
                for p in room.players.values()
            ],
            "count": len(room.players),
        }
        await self._broadcast_all(room, player_list)

    async def _broadcast_all(self, room: GameRoom, data: dict):
        if room.professor_ws:
            try:
                await room.professor_ws.send_json(data)
            except Exception:
                pass

        for player in room.players.values():
            try:
                await player.websocket.send_json(data)
            except Exception:
                pass


# Singleton instance
game_manager = GameManager()
