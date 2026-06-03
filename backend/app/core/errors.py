"""표준 에러 응답: { error: { code, message, meta } }."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """도메인 오류. 모든 4xx를 이 형태로 통일."""

    def __init__(self, status: int, code: str, message: str, meta: dict | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.meta = meta or {}
        super().__init__(message)


def _body(code: str, message: str, meta: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "meta": meta or {}}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status, content=_body(exc.code, exc.message, exc.meta))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content=_body("VALIDATION_ERROR", "입력값이 올바르지 않습니다", {"detail": _safe(exc.errors())}),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        # 404 등 라우팅 단계 오류도 표준 형태로
        code = {401: "TOKEN_EXPIRED", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다"
        return JSONResponse(status_code=exc.status_code, content=_body(code, message))


def _safe(errors) -> list:
    """pydantic 에러에서 직렬화 불가능한 ctx 등을 제거."""
    out = []
    for e in errors:
        out.append({"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")})
    return out


# 자주 쓰는 오류 헬퍼
def validation_error(message: str, meta: dict | None = None) -> AppError:
    return AppError(400, "VALIDATION_ERROR", message, meta)


def forbidden(message: str = "권한이 없습니다") -> AppError:
    return AppError(403, "FORBIDDEN", message)


def not_found(message: str = "해당 항목을 찾을 수 없습니다") -> AppError:
    return AppError(404, "NOT_FOUND", message)
