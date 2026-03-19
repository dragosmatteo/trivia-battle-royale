"""
GameManager - Singleton pattern for managing real-time Battle Royale game sessions.
Handles WebSocket connections, game state, and elimination logic.
"""

import asyncio
import json
import random
import string
import time
from dataclasses import dataclass, field
from fastapi import WebSocket

# Grace period in seconds — answers arriving within this window after timer
# expires are still accepted (compensates for network latency).
ANSWER_GRACE_PERIOD = 2.5


@dataclass
class Player:
    nickname: str
    websocket: WebSocket
    score: int = 0
    is_alive: bool = True
    current_answer: int | None = None
    answer_time: float | None = None
    streak: int = 0


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
    # Mapping from shuffled index → original index for current question
    shuffle_map: list[int] = field(default_factory=list)
    # The original correct_index for the current question (before shuffle)
    original_correct_index: int = -1


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

    async def _next_question(self, room: GameRoom):
        room.current_question_index += 1

        if room.current_question_index >= len(room.questions):
            await self._end_game(room)
            return

        alive_count = sum(1 for p in room.players.values() if p.is_alive)
        if alive_count <= 1:
            await self._end_game(room)
            return

        q = room.questions[room.current_question_index]
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
        room.shuffle_map = indices  # shuffle_map[new_pos] = old_pos

        shuffled_options = [original_options[i] for i in indices]
        # Find where the correct answer ended up after shuffle
        shuffled_correct_index = indices.index(original_correct)

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
        }

        # Send to all players (alive get interactive, spectators get view-only)
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

        # Start timer — add grace period so late answers aren't lost
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
        # Accept answers within time limit + grace period
        if elapsed > room.time_per_question + ANSWER_GRACE_PERIOD:
            return  # Too late, ignore

        player.current_answer = answer
        # Clamp answer_time to time_per_question so late answers don't get
        # negative speed bonus but are still counted as answered
        player.answer_time = min(elapsed, float(room.time_per_question))

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
        # Use the SHUFFLED correct index (where the correct answer ended up
        # after shuffling the options for this round)
        correct = room.shuffle_map.index(room.original_correct_index) if room.shuffle_map else q["correct_index"]

        # Determine if this is a "sudden death" round (last 5 questions or less)
        is_sudden_death = room.current_question_index >= len(room.questions) - 5
        any_correct = False

        results = {}
        for nickname, player in room.players.items():
            if not player.is_alive:
                results[nickname] = {"status": "eliminated_before", "score": player.score}
                continue

            answered_correctly = player.current_answer == correct
            if answered_correctly:
                any_correct = True
                # Score: base points + speed bonus
                time_bonus = max(0, int((room.time_per_question - (player.answer_time or room.time_per_question)) * 10))
                points = 100 + time_bonus
                player.score += points
                player.streak += 1
                # Streak bonus
                if player.streak >= 3:
                    player.score += 50
                results[nickname] = {
                    "status": "correct",
                    "score": player.score,
                    "points_earned": points,
                    "streak": player.streak,
                }
            else:
                player.streak = 0
                if player.current_answer is None:
                    # Didn't answer in time — eliminated
                    player.is_alive = False
                    player.score = max(0, player.score)
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "timeout_eliminated", "score": player.score}
                elif is_sudden_death and any_correct:
                    # Sudden death: wrong answer = eliminated if someone else got it right
                    player.is_alive = False
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "eliminated", "score": player.score}
                else:
                    results[nickname] = {"status": "wrong", "score": player.score}

        # In sudden death, retroactively eliminate wrong answers if any_correct
        if is_sudden_death and any_correct:
            for nickname, player in room.players.items():
                if player.is_alive and player.current_answer != correct and player.current_answer is not None:
                    player.is_alive = False
                    room.eliminated_this_round.append(nickname)
                    results[nickname] = {"status": "eliminated", "score": player.score}

        alive_count = sum(1 for p in room.players.values() if p.is_alive)

        round_result = {
            "type": "round_result",
            "question_index": room.current_question_index,
            "correct_index": correct,
            "explanation": q.get("explanation", ""),
            "eliminated": room.eliminated_this_round,
            "alive_count": alive_count,
            "is_sudden_death": is_sudden_death,
            "leaderboard": self._get_leaderboard(room),
        }

        # Send personalized results to each player
        for nickname, player in room.players.items():
            try:
                personal_result = {
                    **round_result,
                    "your_result": results.get(nickname, {}),
                    "your_answer": player.current_answer,
                    "is_alive": player.is_alive,
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

        # Wait before next question
        await asyncio.sleep(5)

        if alive_count <= 1 or room.current_question_index >= len(room.questions) - 1:
            await self._end_game(room)
        else:
            await self._next_question(room)

    async def _end_game(self, room: GameRoom):
        room.status = "finished"
        leaderboard = self._get_leaderboard(room)

        winner = leaderboard[0]["nickname"] if leaderboard else "Nimeni"

        end_data = {
            "type": "game_over",
            "winner": winner,
            "leaderboard": leaderboard,
            "total_rounds": room.current_question_index + 1,
        }

        await self._broadcast_all(room, end_data)

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
        # Send to professor
        if room.professor_ws:
            try:
                await room.professor_ws.send_json(data)
            except Exception:
                pass

        # Send to all players
        for player in room.players.values():
            try:
                await player.websocket.send_json(data)
            except Exception:
                pass


# Singleton instance
game_manager = GameManager()
