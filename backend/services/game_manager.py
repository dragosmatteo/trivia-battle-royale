"""
GameManager - Singleton pattern for managing real-time Battle Royale game sessions.
Handles WebSocket connections, game state, elimination logic,
round statistics, and adaptive difficulty.
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

# After this many qualifying rounds, players split into difficulty tiers
QUALIFYING_ROUNDS = 3


@dataclass
class Player:
    nickname: str
    websocket: WebSocket
    score: int = 0
    is_alive: bool = True
    current_answer: int | None = None
    answer_time: float | None = None
    streak: int = 0
    correct_count: int = 0      # total correct answers
    total_answered: int = 0     # total questions answered
    difficulty_tier: str = ""   # "", "advanced", "standard"


@dataclass
class GameRoom:
    pin: str
    course_id: int
    professor_id: int
    professor_ws: WebSocket | None = None
    players: dict[str, Player] = field(default_factory=dict)
    questions: list[dict] = field(default_factory=list)
    current_question_index: int = -1
    status: str = "waiting"  # waiting, playing, round_active, round_ended, finished
    time_per_question: int = 30
    round_start_time: float = 0
    eliminated_this_round: list[str] = field(default_factory=list)
    # Mapping from shuffled index -> original index for current question
    shuffle_map: list[int] = field(default_factory=list)
    # The original correct_index for the current question (before shuffle)
    original_correct_index: int = -1
    # Round history for statistics
    round_history: list[dict] = field(default_factory=list)
    # Whether difficulty tiers have been assigned
    tiers_assigned: bool = False


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
            await ws.send_json({"type": "error", "message": "Sesiunea nu este disponibilă"})
            return False

        if nickname in room.players:
            await ws.send_json({"type": "error", "message": "Nickname-ul este deja folosit"})
            return False

        room.players[nickname] = Player(nickname=nickname, websocket=ws)

        # Notify player
        await ws.send_json({
            "type": "joined",
            "nickname": nickname,
            "players_count": len(room.players),
        })

        # Notify professor and all players about new player
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

    def _assign_difficulty_tiers(self, room: GameRoom):
        """After qualifying rounds, split players into difficulty tiers."""
        if room.tiers_assigned:
            return

        alive_players = [p for p in room.players.values() if p.is_alive]
        if len(alive_players) < 2:
            return

        # Calculate accuracy for each player
        for p in alive_players:
            p._accuracy = p.correct_count / max(p.total_answered, 1)

        # Sort by accuracy descending
        alive_players.sort(key=lambda p: p._accuracy, reverse=True)

        # Top half = advanced, bottom half = standard
        mid = len(alive_players) // 2
        for i, p in enumerate(alive_players):
            p.difficulty_tier = "advanced" if i < mid else "standard"

        room.tiers_assigned = True

        # Clean up temp attribute
        for p in alive_players:
            if hasattr(p, '_accuracy'):
                del p._accuracy

    def _select_question_for_round(self, room: GameRoom) -> dict:
        """Select the next question, considering adaptive difficulty after qualifying."""
        q = room.questions[room.current_question_index]

        # After qualifying rounds, try to pick difficulty-appropriate questions
        if room.tiers_assigned and room.current_question_index < len(room.questions):
            # Count alive players per tier
            alive = [p for p in room.players.values() if p.is_alive]
            advanced_count = sum(1 for p in alive if p.difficulty_tier == "advanced")
            standard_count = sum(1 for p in alive if p.difficulty_tier == "standard")

            # If mostly advanced players alive, prefer harder questions
            if advanced_count > standard_count:
                # Look ahead for a hard question
                for i in range(room.current_question_index, min(room.current_question_index + 3, len(room.questions))):
                    if room.questions[i].get("difficulty") == "hard":
                        # Swap current with hard question
                        room.questions[room.current_question_index], room.questions[i] = \
                            room.questions[i], room.questions[room.current_question_index]
                        q = room.questions[room.current_question_index]
                        break
            elif standard_count > advanced_count:
                # Look ahead for an easy question
                for i in range(room.current_question_index, min(room.current_question_index + 3, len(room.questions))):
                    if room.questions[i].get("difficulty") == "easy":
                        room.questions[room.current_question_index], room.questions[i] = \
                            room.questions[i], room.questions[room.current_question_index]
                        q = room.questions[room.current_question_index]
                        break

        return q

    async def _next_question(self, room: GameRoom):
        room.current_question_index += 1

        if room.current_question_index >= len(room.questions):
            await self._end_game(room)
            return

        alive_count = sum(1 for p in room.players.values() if p.is_alive)
        if alive_count <= 1:
            await self._end_game(room)
            return

        # After qualifying rounds, assign difficulty tiers
        if room.current_question_index == QUALIFYING_ROUNDS and not room.tiers_assigned:
            self._assign_difficulty_tiers(room)
            # Notify all players of their tier
            for player in room.players.values():
                if player.difficulty_tier and player.is_alive:
                    tier_label = "Arena Avansata" if player.difficulty_tier == "advanced" else "Arena Standard"
                    try:
                        await player.websocket.send_json({
                            "type": "tier_assigned",
                            "tier": player.difficulty_tier,
                            "tier_label": tier_label,
                            "message": f"Faza de calificare completă! Ai fost repartizat în {tier_label}.",
                        })
                    except Exception:
                        pass

        # Select question (may adapt difficulty)
        q = self._select_question_for_round(room)

        room.status = "round_active"
        room.round_start_time = time.time()
        room.eliminated_this_round = []

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
        phase = "Calificare" if room.current_question_index < QUALIFYING_ROUNDS else ""
        if room.tiers_assigned:
            phase = "Arena Adaptivă"
        if room.current_question_index >= len(room.questions) - 5:
            phase = "Sudden Death"

        # Send question to all players (WITHOUT correct answer!)
        question_data = {
            "type": "question",
            "index": room.current_question_index,
            "total": len(room.questions),
            "question_text": q["question_text"],
            "options": shuffled_options,
            "difficulty": q.get("difficulty", "medium"),
            "time_limit": room.time_per_question,
            "alive_count": alive_count,
            "phase": phase,
        }

        # Send to all players
        for player in room.players.values():
            try:
                player_data = {**question_data}
                if player.difficulty_tier:
                    player_data["your_tier"] = player.difficulty_tier
                await player.websocket.send_json(player_data)
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
        if not player or not player.is_alive or player.current_answer is not None:
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

        # Check if all alive players have answered
        alive_players = [p for p in room.players.values() if p.is_alive]
        all_answered = all(p.current_answer is not None for p in alive_players)

        if all_answered:
            await self._end_round(room)

    async def _end_round(self, room: GameRoom):
        if room.status != "round_active":
            return

        room.status = "round_ended"
        q = room.questions[room.current_question_index]
        correct = room.shuffle_map.index(room.original_correct_index) if room.shuffle_map else q["correct_index"]

        # Determine if this is a "sudden death" round
        is_sudden_death = room.current_question_index >= len(room.questions) - 5
        any_correct = False

        # --- Compute round statistics ---
        alive_players = [p for p in room.players.values() if p.is_alive]
        total_alive = len(alive_players)
        correct_count = 0
        wrong_count = 0
        timeout_count = 0
        answer_times = []
        fastest_player = None
        fastest_time = float('inf')

        results = {}
        for nickname, player in room.players.items():
            if not player.is_alive:
                results[nickname] = {"status": "eliminated_before", "score": player.score}
                continue

            answered_correctly = player.current_answer == correct
            if answered_correctly:
                any_correct = True
                correct_count += 1
                player.correct_count += 1
                # Score: base points + speed bonus
                time_bonus = max(0, int((room.time_per_question - (player.answer_time or room.time_per_question)) * 10))
                points = 100 + time_bonus
                player.score += points
                player.streak += 1
                if player.streak >= 3:
                    player.score += 50
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
                player.streak = 0
                if player.current_answer is None:
                    timeout_count += 1
                    player.is_alive = False
                    player.score = max(0, player.score)
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "timeout_eliminated", "score": player.score}
                elif is_sudden_death and any_correct:
                    wrong_count += 1
                    player.is_alive = False
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "eliminated", "score": player.score}
                else:
                    wrong_count += 1
                    results[nickname] = {"status": "wrong", "score": player.score}
                    if player.answer_time:
                        answer_times.append(player.answer_time)

        # In sudden death, retroactively eliminate wrong answers
        if is_sudden_death and any_correct:
            for nickname, player in room.players.items():
                if player.is_alive and player.current_answer != correct and player.current_answer is not None:
                    player.is_alive = False
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "eliminated", "score": player.score}

        alive_count = sum(1 for p in room.players.values() if p.is_alive)

        # Build statistics
        accuracy_pct = round((correct_count / total_alive * 100)) if total_alive > 0 else 0
        avg_time = round(sum(answer_times) / len(answer_times), 1) if answer_times else 0

        round_stats = {
            "total_players": total_alive,
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
            "eliminated": room.eliminated_this_round,
            "alive_count": alive_count,
            "is_sudden_death": is_sudden_death,
            "leaderboard": self._get_leaderboard(room),
            "round_stats": round_stats,
            "options": shuffled_options,
        }

        # Send personalized results to each player
        for nickname, player in room.players.items():
            try:
                personal_result = {
                    **round_result,
                    "your_result": results.get(nickname, {}),
                    "your_answer": player.current_answer,
                    "is_alive": player.is_alive,
                    "your_score": player.score,
                    "your_accuracy": round(player.correct_count / max(player.total_answered, 1) * 100),
                    "your_streak": player.streak,
                    "your_tier": player.difficulty_tier,
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

        # Wait before next question (longer to read stats)
        await asyncio.sleep(7)

        if alive_count <= 1 or room.current_question_index >= len(room.questions) - 1:
            await self._end_game(room)
        else:
            await self._next_question(room)

    async def _end_game(self, room: GameRoom):
        room.status = "finished"
        leaderboard = self._get_leaderboard(room)

        winner = leaderboard[0]["nickname"] if leaderboard else "Nimeni"

        # Final statistics
        total_rounds = room.current_question_index + 1
        game_stats = {
            "total_rounds": total_rounds,
            "total_players": len(room.players),
            "survivors": sum(1 for p in room.players.values() if p.is_alive),
        }

        end_data = {
            "type": "game_over",
            "winner": winner,
            "leaderboard": leaderboard,
            "total_rounds": total_rounds,
            "game_stats": game_stats,
        }

        await self._broadcast_all(room, end_data)

        # --- Save results to database ---
        await self._save_results_to_db(room)

    async def _save_results_to_db(self, room: GameRoom):
        """Persist final game results into game_results and update game_sessions."""
        try:
            from models.database import get_db
            db = await get_db()

            # Find the session id by pin_code
            cursor = await db.execute(
                "SELECT id FROM game_sessions WHERE pin_code = ?", (room.pin,)
            )
            session_row = await cursor.fetchone()
            if not session_row:
                await db.close()
                return

            session_id = session_row["id"]
            finished_at = datetime.now(timezone.utc).isoformat()

            # Update session status to finished
            await db.execute(
                "UPDATE game_sessions SET status = 'finished' WHERE id = ?",
                (session_id,),
            )

            # Determine elimination round for each player
            # Players who are still alive were never eliminated
            for player in room.players.values():
                eliminated_round = None
                if not player.is_alive:
                    # Check round_history to find when this player was eliminated
                    for rh in room.round_history:
                        q_idx = rh["question_index"]
                        # We don't track per-player elimination in round_history directly,
                        # so we estimate: the player was eliminated at the round
                        # equal to the number of questions they answered (total_answered)
                        pass
                    # Best estimate: eliminated at the round = total_answered (0-indexed)
                    eliminated_round = player.total_answered if player.total_answered > 0 else 1

                await db.execute(
                    """INSERT INTO game_results
                       (session_id, player_name, user_id, score, is_alive, eliminated_at_round, finished_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session_id,
                        player.nickname,
                        None,  # user_id not tracked in current WebSocket flow
                        player.score,
                        1 if player.is_alive else 0,
                        eliminated_round,
                        finished_at,
                    ),
                )

            await db.commit()
            await db.close()
        except Exception as e:
            print(f"Error saving game results: {e}")

    def _get_leaderboard(self, room: GameRoom) -> list[dict]:
        players = sorted(
            room.players.values(),
            key=lambda p: (-int(p.is_alive), -p.score),
        )
        return [
            {
                "rank": i + 1,
                "nickname": p.nickname,
                "score": p.score,
                "is_alive": p.is_alive,
                "streak": p.streak,
                "correct_count": p.correct_count,
                "total_answered": p.total_answered,
                "accuracy": round(p.correct_count / max(p.total_answered, 1) * 100),
                "tier": p.difficulty_tier,
            }
            for i, p in enumerate(players)
        ]

    async def _broadcast_player_list(self, room: GameRoom):
        player_list = {
            "type": "player_list",
            "players": [
                {"nickname": p.nickname, "is_alive": p.is_alive}
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
