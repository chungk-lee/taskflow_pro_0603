"""Vercel Python Serverless Function: FastAPI ASGI 앱 노출.

vercel.json의 rewrite가 정적 파일(public/)에 매칭되지 않는 모든 경로를
이 함수로 보낸다. FastAPI는 원래 요청 경로(/auth/*, /teams/*, /docs ...)를 그대로 받는다.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "backend"))

from app.main import app  # noqa: E402,F401
