"""Vercel 진입점: backend/app 의 FastAPI 인스턴스를 노출한다.

Vercel은 루트의 index.py에서 `app`(ASGI)을 자동 인식한다.
정적 프론트엔드는 public/ 에서 자동 서빙되고, 그 외 경로는 이 함수로 라우팅된다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.main import app  # noqa: E402,F401
