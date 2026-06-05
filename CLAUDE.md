# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 현재 상태

MVP 구현·배포 완료 단계다. 백엔드(FastAPI 18 API)·프론트엔드(Vanilla JS SPA)가 모두 구현됐고 Vercel에 배포돼 동작한다.

- 백엔드: `backend/app/` — FastAPI 앱, 18 API, JWT/bcrypt, 표준 에러, 권한, KST, SQLite↔Postgres
- 프론트: `public/` — Vanilla JS + Tailwind SPA(해시 라우터), 칸반·채팅·팀 관리 화면
- 배포: `api/index.py`(Vercel Python 함수) + `public/`(정적) + `vercel.json`(rewrite). `main` push 시 자동 배포
- 테스트: `backend/tests/` — pytest 51개(Auth/Team/Task/Chat 전 흐름·권한·에러), in-memory SQLite 격리
- 기획 원본: `docs/TaskFlow_프로그램정의.pdf`(미션·기능·DB·API·NFR), `docs/TaskFlow_스토리보드.pdf`(42슬라이드, 화면/에러 케이스, 결정 8건, ER·API 명세)
- 스펙: `openspec/changes/taskflow-mvp/` — proposal/design/specs/tasks

스토리보드 v2는 프로그램정의 PDF의 빈틈을 **결정 8건**(아래)으로 메운 통합본이며, **두 PDF가 충돌할 경우 스토리보드 v2가 우선한다.**

## 프로젝트 개요

**미션:** 소규모 팀(≤5명)이 칸반 + 실시간 채팅으로 업무 진행을 한 화면에서 추적.

**기술 스택 (사용자가 확정 — 임의 변경 금지):**
- 백엔드: FastAPI (Python, async). 로컬 SQLite 파일 ↔ 운영 Neon(PostgreSQL)을 `DATABASE_URL` 환경변수로만 전환
- 프론트엔드: Vanilla JS (ES6+, fetch API) + Tailwind CSS. 프레임워크 없음
- 배포: Vercel (프론트 정적 파일 + 백엔드 Serverless Functions), DB는 Vercel Storage Neon. `main` push 시 자동 배포

**클로드코드 위임 영역(스펙이 지정하지 않음, 구현 시 판단):** 라이브러리 선택(SQLAlchemy/Tortoise·pydantic·bcrypt·python-jose 등), 디렉토리 구조, 마이그레이션 도구, 프론트 파일 구조(SPA vs MPA)·라우팅·CSS 빌드(CDN vs 빌드)·상태 관리.

## 개발/실행

로컬 실행(가상환경은 `backend/.venv`):
- 백엔드: `backend/`에서 `uvicorn app.main:app --reload` (기본 SQLite 파일 `sqlite:///./taskflow.db`)
- Swagger UI: `http://127.0.0.1:8000/docs` (ReDoc은 `/redoc`, 스키마는 `/openapi.json`). 18 API를 브라우저에서 직접 호출/검증 가능.
- 프론트: `public/`에서 `python -m http.server` 또는 live-server로 정적 서빙. `api.js`가 로컬이면 `http://127.0.0.1:8000`, 배포면 same-origin으로 자동 분기.
- 로컬 SQLite 파일(`*.db`)은 git에서 제외(.gitignore).

**테스트는 범위에 포함한다(결정 #7 override — 사용자 지시).** 원래 스토리보드 결정 #7은 "테스트 자동화 범위 외, 수동 확인"이었으나, 사용자가 Swagger + 테스트 코드 작성을 명시 요청해 백엔드 pytest 스위트를 채택했다.
- 실행: `backend/`에서 `.venv/Scripts/python.exe -m pytest` (현재 51개 통과)
- 위치: `backend/tests/` — `conftest.py`(in-memory SQLite + `get_db` 오버라이드로 테스트마다 격리), `test_auth/teams/tasks/chat.py`
- 프론트는 자동화 테스트 없이 Playwright/수동으로 정성 확인. 성능 기준(API 100ms, 드래그 50ms, 신규 합류 1분 컨텍스트 파악)도 자동 측정 없이 정성 검증(결정 #7).

## 데이터 모델 (4테이블, 통합본 기준)

`★`는 스토리보드가 프로그램정의 PDF에 추가/변경한 항목이다.

- **users**: id PK · email UNIQUE NOT NULL · password_hash NOT NULL · `★ team_id` FK→teams NULL · created_at
- **teams**: id PK · name NOT NULL(1–30자) · invite_code UNIQUE(형식 `AAAA-9999`) · owner_id FK→users NOT NULL · created_at
- **tasks**: id PK · team_id FK→teams NOT NULL · title NOT NULL(1–100자) · status `TODO|DOING|DONE` · creator_id FK→users NOT NULL · `★ assignee_id` FK→users NULL · `★ created_at`(정렬용)
- **messages**: id PK · team_id FK→teams NOT NULL · user_id FK→users NOT NULL · content NOT NULL(1–1000자) · created_at

**핵심 관계/규칙:**
- **1인 1팀**: `users.team_id`가 사용자의 소속을 결정. NULL = 미가입. 한 사용자는 동시에 한 팀만 소속(결정 #1).
- **'내 태스크' = `WHERE assignee_id = current_user_id`** (creator_id 아님). assignee_id는 nullable이며 NULL은 "미할당"(결정 #4).
- 인덱스: `tasks(team_id, created_at)`(칸반 정렬), `messages(team_id, id)`(채팅 폴링 `since_id=` 증분), `teams(invite_code)` UNIQUE, `users.team_id`.

## API 18개 (그룹별)

Auth 4 + Team 5 + Task 6 + Chat 3 = 18.

```
Auth   POST /auth/signup            이메일+비번 → 201 + JWT
       POST /auth/login             → 200 + JWT (exp 24h)
       POST /auth/logout            stateless, 200만 반환
       GET  /auth/me                현재 사용자 정보

Team   POST   /teams                팀 생성 + invite_code 자동 발급, owner_id=생성자, users.team_id UPDATE
       POST   /teams/join           invite_code로 합류 → users.team_id UPDATE
       GET    /teams/{id}           팀 정보 (결정 #8: GET /messages/{id} 제거 후 대체)
       GET    /teams/{id}/members   멤버 목록
       DELETE /teams/{id}/leave     팀 떠나기(자기 자신)

Task   GET    /teams/{id}/tasks        칸반 조회 (filter: 전체/@me/미할당)
       POST   /teams/{id}/tasks        카드 생성
       GET    /tasks/{id}              단일 카드 상세
       PUT    /tasks/{id}              제목·assignee 수정
       PATCH  /tasks/{id}/status       ★ 결정 #3: 상태 이동(드래그) 전용으로 분리
       DELETE /tasks/{id}              creator OR team owner만

Chat   GET    /teams/{id}/messages     ?since_id= 증분 폴링(5초). since_id 없으면 최근 50개
       POST   /teams/{id}/messages     1000자 이내(클라+서버 양쪽 검증)
       DELETE /messages/{id}           본인 메시지만 (결정 #6)
```

## 권한 모델 (반드시 구현)

- 모든 `/teams/*` 라우트는 JWT + `user.team_id == {id}` 멤버십을 확인. 비멤버는 읽기/쓰기 모두 **403 FORBIDDEN**.
- **DELETE /tasks/{id}**: creator 또는 team owner만. owner는 타인 카드도 삭제 가능(오버라이드). member는 본인 카드만.
- **DELETE /messages/{id}**: 본인 메시지만. owner라도 타인 메시지 삭제 불가 → **403 NOT_OWNER**.
- 추방·역할 변경은 범위 외. 권한은 team `owner`(1명) / `member`(N명) 2단계만.

## 에러 응답 표준

모든 4xx/5xx는 동일 형태로 반환한다:

```json
{ "error": { "code": "<SCREAMING_SNAKE>", "message": "<한국어 사용자 메시지>", "meta": { } } }
```

`meta`는 옵션(예: TOO_LONG의 `limit`/`actual`). 보안상 민감정보(이메일 존재 여부 등)를 노출하지 않는다.

| HTTP | code | 발생 조건 |
|------|------|-----------|
| 400 | VALIDATION_ERROR | 필드 형식 오류(이메일/길이/필수) |
| 400 | TOO_LONG | 메시지 1000자 초과 |
| 401 | INVALID_CREDENTIALS | 로그인 실패(이메일 존재 여부 비노출, 동일 메시지) |
| 401 | TOKEN_EXPIRED | JWT 만료/누락 |
| 403 | FORBIDDEN | 비멤버의 `/teams/{id}/*` 접근 |
| 403 | NOT_OWNER | 타인 메시지 삭제 시도 |
| 404 | NOT_FOUND | 초대코드/리소스 없음 |
| 409 | EMAIL_TAKEN | 회원가입 중복 이메일 |

## 인증/세션 흐름

- 로그인 성공 시 JWT(24h)를 `localStorage`에 저장. 갱신 토큰 없음 → 만료 시 무조건 재로그인.
- 로그인 후 분기: `users.team_id == NULL` → 팀 선택 화면 강제, 그 외 → `/teams/{team_id}` 칸반.
- 로그아웃은 stateless(결정 #5): 서버 블랙리스트 없이 200만 반환, 클라이언트가 토큰 폐기.
- API 401 응답 시 클라이언트가 토큰 삭제 후 `/login`으로 redirect(직전 URL 저장 안 함).

## 도메인 규칙 상수

- 초대코드 형식: 정규식 `^[A-Z]{4}-[0-9]{4}$` (예: `FRNT-2026`). 클라+서버 양쪽 검증. 팀당 1개 고정, 재발급 없음.
- 비밀번호: 8자 이상(클라 검증) + bcrypt 해시 저장(서버, 평문 저장 금지).
- 메시지: 1000자 이내. 채팅 폴링은 5초 간격(모바일 입력 포커스 시 2초), `since_id=` 마지막 메시지 **id**로 증분 수신(시각 기반 대신 id 커서 — 동시 전송 시 누락/중복 방지).
- 시간대: 서버·클라이언트 모두 KST 가정(UTC 변환 안 함). UI는 한국어만.

## 범위 외 (구현하지 말 것)

알림(이메일/SMS/푸시) · 파일/이미지 첨부 · 전문 검색(단순 SELECT만) · 페이지별 권한 세분화 · 다국어 · WebSocket(5초 폴링으로 대체) · 로그인 실패 cooldown · JWT 갱신 토큰 · 팀 추방/역할 변경 · 관측성 도구(Sentry/로그 수집, print 디버깅만).

> ~~테스트 자동화~~는 결정 #7 override(사용자 지시)로 범위에 포함됨 — 백엔드 pytest 스위트 채택. 위 "개발/실행" 참조.

## 통합본 결정 8건 (스토리보드 A·03 — 충돌 시 이 결정이 기준)

1. `users.team_id` 추가(1인 1팀) — 멤버십 정의
2. 신규 합류자: 채팅 이력 '검색' → 시간순 '스크롤'(검색은 범위 외)
3. `PUT /tasks/{id}`(status) 중복 제거 → `PATCH /tasks/{id}/status`로 분리
4. `tasks.assignee_id`(nullable) 추가 — '내 태스크' = assignee 기준
5. logout stateless — 200만, 블랙리스트 없음
6. 권한: 비멤버 403, DELETE task는 creator/owner, DELETE message는 본인만
7. 측정 불가 NFR(드래그 50ms·1분 파악)은 정성 검증으로 명시
8. 모호한 `GET /messages/{id}` 제거 → `GET /teams/{id}`로 교체(API 18개 유지)
