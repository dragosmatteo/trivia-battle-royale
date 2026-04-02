import re
from pydantic import BaseModel, Field, field_validator
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
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole
    group_name: Optional[str] = ""

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Username-ul poate contine doar litere, cifre, punct, cratima si underscore")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Adresa de email invalida")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Parola trebuie sa aiba minim 6 caractere")
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Parola trebuie sa contina cel putin o litera")
        if not re.search(r'[0-9]', v):
            raise ValueError("Parola trebuie sa contina cel putin o cifra")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[a-zA-ZăâîșțĂÂÎȘȚéèêëàùûüôöïçÉÈÊËÀÙÛÜÔÖÏÇ\s.\-]+$', v):
            raise ValueError("Numele poate contine doar litere, spatii, punct si cratima")
        return v

    @field_validator("group_name")
    @classmethod
    def validate_group_name(cls, v: str | None) -> str:
        if not v:
            return ""
        v = v.strip()
        if len(v) > 20:
            raise ValueError("Numele grupei este prea lung (max 20 caractere)")
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Numele grupei poate contine doar litere, cifre, punct si cratima")
        return v


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


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
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = ""


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    professor_id: int
    pdf_filename: Optional[str]
    created_at: str


class MaterialResponse(BaseModel):
    id: int
    course_id: int
    original_name: str
    file_size: int
    char_count: int
    status: str
    error_message: str
    created_at: str


# --- Question Schemas ---
class QuestionSchema(BaseModel):
    question_text: str = Field(..., min_length=10, max_length=1000)
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str = Field(default="", max_length=2000)
    difficulty: Difficulty = Difficulty.medium

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        for i, opt in enumerate(v):
            if not opt or len(opt.strip()) < 1:
                raise ValueError(f"Optiunea {i+1} nu poate fi goala")
            if len(opt) > 500:
                raise ValueError(f"Optiunea {i+1} este prea lunga (max 500 caractere)")
        return [opt.strip() for opt in v]


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
    chapter_hint: Optional[str] = Field(default=None, max_length=200)


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
    pin_code: str = Field(..., pattern=r'^\d{6}$')
    nickname: str = Field(..., min_length=2, max_length=20)


class AnswerSubmission(BaseModel):
    question_index: int
    selected_option: int = Field(..., ge=0, le=3)


class PlayerState(BaseModel):
    nickname: str
    score: int = 0
    is_alive: bool = True
    streak: int = 0


# --- Password Schemas ---
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Parola nouă trebuie să conțină cel puțin o literă")
        if not re.search(r'[0-9]', v):
            raise ValueError("Parola nouă trebuie să conțină cel puțin o cifră")
        return v


class ResetPasswordRequest(BaseModel):
    user_id: int
