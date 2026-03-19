from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    professor = "professor"
    student = "student"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# --- Auth Schemas ---
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=4)
    full_name: str
    role: UserRole
    group_name: Optional[str] = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    group_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Course Schemas ---
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = ""


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    professor_id: int
    pdf_filename: Optional[str]
    created_at: str


# --- Question Schemas ---
class QuestionSchema(BaseModel):
    question_text: str
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str = ""
    difficulty: Difficulty = Difficulty.medium


class QuestionResponse(BaseModel):
    id: int
    course_id: int
    question_text: str
    options: list[str]
    correct_index: int
    explanation: str
    difficulty: str


class GenerateRequest(BaseModel):
    course_id: int
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Optional[Difficulty] = None
    chapter_hint: Optional[str] = None


# --- Game Schemas ---
class GameSessionCreate(BaseModel):
    course_id: int
    num_questions: int = Field(default=10, ge=3, le=30)
    time_per_question: int = Field(default=30, ge=10, le=120)


class GameSessionResponse(BaseModel):
    id: int
    pin_code: str
    course_id: int
    status: str
    time_per_question: int
    created_at: str


class JoinGameRequest(BaseModel):
    pin_code: str
    nickname: str = Field(..., min_length=2, max_length=20)


class AnswerSubmission(BaseModel):
    question_index: int
    selected_option: int


class PlayerState(BaseModel):
    nickname: str
    score: int = 0
    is_alive: bool = True
    streak: int = 0
