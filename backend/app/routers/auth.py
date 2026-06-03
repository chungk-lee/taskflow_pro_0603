"""Auth API (4): signup / login / logout / me."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user
from ..core.errors import AppError
from ..core.security import create_access_token, hash_password, verify_password
from ..models import User
from ..schemas import LoginRequest, OkOut, SignupRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED, summary="회원가입")
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == body.email))
    if exists:
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일입니다")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut, summary="로그인")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    # 이메일 존재 여부 비노출: 동일한 메시지
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다")
    return TokenOut(token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/logout", response_model=OkOut, summary="로그아웃(stateless)")
def logout(_: User = Depends(get_current_user)):
    # 서버 블랙리스트 없음. 토큰 폐기는 클라이언트가 수행.
    return OkOut()


@router.get("/me", response_model=UserOut, summary="현재 사용자")
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
