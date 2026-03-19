from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from fastapi import APIRouter, HTTPException, Depends
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.database import get_db
from models.schemas import UserCreate, UserLogin, Token, UserResponse
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


def hash_password(password: str) -> str:
    return sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalid")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")

    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
    user = await cursor.fetchone()
    await db.close()

    if not user:
        raise HTTPException(status_code=401, detail="Utilizator negăsit")

    return dict(user)


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    db = await get_db()
    # Check existing
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (user_data.username, user_data.email),
    )
    if await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=400, detail="Username sau email deja existent")

    hashed = hash_password(user_data.password)
    cursor = await db.execute(
        "INSERT INTO users (username, email, hashed_password, full_name, role, group_name) VALUES (?, ?, ?, ?, ?, ?)",
        (user_data.username, user_data.email, hashed, user_data.full_name, user_data.role.value, user_data.group_name or ""),
    )
    await db.commit()
    user_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(await cursor.fetchone())
    await db.close()

    token = create_access_token({"sub": str(user_id), "role": user["role"]})
    return Token(
        access_token=token,
        user=UserResponse(
            id=user["id"], username=user["username"], email=user["email"],
            full_name=user["full_name"], role=user["role"], group_name=user["group_name"],
        ),
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE username = ?", (credentials.username,))
    user = await cursor.fetchone()
    await db.close()

    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Credențiale invalide")

    user = dict(user)
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return Token(
        access_token=token,
        user=UserResponse(
            id=user["id"], username=user["username"], email=user["email"],
            full_name=user["full_name"], role=user["role"], group_name=user["group_name"],
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"], username=user["username"], email=user["email"],
        full_name=user["full_name"], role=user["role"], group_name=user["group_name"],
    )
