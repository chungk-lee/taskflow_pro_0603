## 1. 프로젝트 부트스트랩 (백엔드)

- [x] 1.1 백엔드 디렉토리 구조 생성(app/ 라우터·모델·스키마·core 분리) 및 `requirements.txt`(FastAPI, uvicorn, SQLAlchemy, pydantic, passlib[bcrypt], python-jose, httpx, pytest) 추가
- [x] 1.2 설정 로더(`core/config.py`): `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` 환경변수 + 로컬 기본값
- [x] 1.3 DB 엔진/세션(`core/db.py`): SQLAlchemy로 SQLite↔Postgres 호환, 세션 의존성
- [x] 1.4 `.gitignore`에 로컬 SQLite 파일(`*.db`)·`.env`·`__pycache__` 추가
- [x] 1.5 FastAPI 앱 엔트리(`main.py`) 생성, CORS 미들웨어를 `CORS_ORIGINS` 허용목록으로 구성

## 2. 데이터 모델 & 마이그레이션

- [x] 2.1 `users`(id, email UNIQUE NOT NULL, password_hash, team_id FK NULL, created_at) 모델
- [x] 2.2 `teams`(id, name 1–30자, invite_code UNIQUE `AAAA-9999`, owner_id FK NOT NULL, created_at) 모델
- [x] 2.3 `tasks`(id, team_id FK NOT NULL, title 1–100자, status enum, creator_id FK, assignee_id FK NULL, created_at) 모델 + FK CASCADE
- [x] 2.4 `messages`(id, team_id FK NOT NULL, user_id FK NOT NULL, content 1–1000자, created_at) 모델 + FK CASCADE
- [x] 2.5 인덱스 생성: `tasks(team_id, created_at)`, `messages(team_id, id)`, `teams(invite_code)` UNIQUE, `users.team_id`
- [x] 2.6 스키마 초기화(create_all 또는 Alembic) 및 KST(+09:00) timezone-aware 기본 시각 적용

## 3. 공통 인프라 (에러·인증·권한)

- [x] 3.1 `AppError(code, message, status, meta)` + 전역 exception handler로 `{error:{code,message,meta}}` 직렬화
- [x] 3.2 `RequestValidationError` → 400 `VALIDATION_ERROR` 매핑
- [x] 3.3 비밀번호 해시 유틸(bcrypt) 및 JWT 발급/검증 유틸(exp 24h)
- [x] 3.4 `get_current_user` 의존성(만료/누락 → 401 `TOKEN_EXPIRED`)
- [x] 3.5 `require_team_member(team_id)` 의존성(비멤버 → 403 `FORBIDDEN`)
- [x] 3.6 초대코드 생성기(`^[A-Z]{4}-[0-9]{4}$`, UNIQUE 충돌 재시도)

## 4. Auth API (4)

- [x] 4.1 `POST /auth/signup` — 201 + JWT, 중복 409 `EMAIL_TAKEN`, 형식 400
- [x] 4.2 `POST /auth/login` — 200 + JWT, 실패 401 `INVALID_CREDENTIALS`(이메일 존재 비노출)
- [x] 4.3 `POST /auth/logout` — stateless 200
- [x] 4.4 `GET /auth/me` — 현재 사용자 `{id,email,team_id}`

## 5. Team API (5)

- [x] 5.1 `POST /teams` — 생성+invite_code 발급, owner 지정, `users.team_id` UPDATE
- [x] 5.2 `POST /teams/join` — `team_id IS NULL`만 허용, 형식400/미존재404/중복409 `ALREADY_IN_TEAM`
- [x] 5.3 `GET /teams/{id}` — `{id,name,invite_code,owner_id,owner_email,member_count,task_count,created_at}`
- [x] 5.4 `GET /teams/{id}/members` — owner/member role 포함 목록
- [x] 5.5 `DELETE /teams/{id}/leave` — member 탈퇴, 단독 owner는 팀 CASCADE 삭제, 멤버 잔존 owner는 409 `OWNER_CANNOT_LEAVE`

## 6. Task API (6)

- [x] 6.1 `GET /teams/{id}/tasks` — 필터(전체/@me/미할당), `created_at DESC`
- [x] 6.2 `POST /teams/{id}/tasks` — 생성(title 1–100자, creator=현재), assignee 팀 멤버 한정 검증
- [x] 6.3 `GET /tasks/{id}` — 단일 상세
- [x] 6.4 `PUT /tasks/{id}` — title·assignee 수정(assignee 팀 한정), status 변경 금지
- [x] 6.5 `PATCH /tasks/{id}/status` — status enum 이동(드래그 전용)
- [x] 6.6 `DELETE /tasks/{id}` — creator/owner만, 그 외 403 `FORBIDDEN`

## 7. Chat API (3)

- [x] 7.1 `POST /teams/{id}/messages` — 1–1000자, 초과 400 `TOO_LONG`(meta limit/actual)
- [x] 7.2 `GET /teams/{id}/messages` — `since_id` 증분(`id>since_id ASC`), 없으면 최근 50개, id 포함
- [x] 7.3 `DELETE /messages/{id}` — 본인만, 타인(owner 포함) 403 `NOT_OWNER`

## 8. Swagger / OpenAPI 문서화

- [x] 8.1 모든 라우트에 태그(Auth/Team/Task/Chat)·`response_model`·summary 부여
- [x] 8.2 표준 에러 스키마를 OpenAPI responses에 등록(주요 4xx 예시 포함)
- [x] 8.3 Bearer 인증 스킴 등록 → `/docs`에서 Authorize 후 호출 가능 확인, `/redoc` 노출 확인

## 9. 백엔드 자동 테스트 (pytest)

- [x] 9.1 pytest 픽스처: 임시/격리 DB, TestClient, 사용자·팀·JWT 생성 헬퍼
- [x] 9.2 Auth 테스트(정상/중복/형식/자격증명/만료)
- [x] 9.3 Team 테스트(생성·합류·중복소속409·owner leave 규칙·비멤버403)
- [x] 9.4 Task 테스트(필터·assignee 팀한정·status 이동·DELETE 권한 매트릭스)
- [x] 9.5 Chat 테스트(`since_id` 무손실·1000자 초과400·삭제 본인만)
- [x] 9.6 권한 격리 회귀(team=1이 team=2 접근 → 전부 403)

## 10. 프론트엔드 (Vanilla JS + Tailwind)

- [x] 10.1 정적 구조·Tailwind 설정(CDN 또는 빌드)·공통 API 클라이언트(fetch, JWT 헤더 자동, 401 redirect)
- [x] 10.2 로그인·회원가입 화면(클라 검증: 이메일·8자) + 에러 표시
- [x] 10.3 팀 선택(미가입)·팀 생성/초대코드 복사·합류 화면
- [x] 10.4 칸반 화면(3컬럼·필터·정렬·카드)·empty state
- [x] 10.5 카드 생성 인라인 입력·상세/수정 모달·삭제 확인(권한별 버튼 노출)
- [x] 10.6 칸반 드래그앤드롭 → `PATCH /tasks/{id}/status`
- [x] 10.7 채팅 화면·말풍선·1000자 카운터·`since_id` 5초 폴링(모바일 2초)·폴링 실패 표시
- [x] 10.8 멤버 목록·403 화면·세션 가드(team_id 분기)
- [x] 10.9 반응형(모바일 햄버거·칸반 스와이프·풀스크린 채팅)

## 11. 배포 & 마무리

- [x] 11.1 `vercel.json`: 프론트 정적 + 백엔드 ASGI Serverless Functions 엔트리 구성
- [x] 11.2 Neon(Vercel Storage) 연결, 운영 `DATABASE_URL`·`JWT_SECRET`·`CORS_ORIGINS` 환경변수 설정
- [x] 11.3 로컬 수동 동작 확인(기능 5종 정상 흐름) + `pytest` 통과 + `/docs`에서 18개 API 확인
- [x] 11.4 `CLAUDE.md` 갱신: 결정 #7 override(테스트 자동화 포함)·Swagger·확정된 8건 설계 반영
- [x] 11.5 `main` push → Vercel 자동 배포 확인
