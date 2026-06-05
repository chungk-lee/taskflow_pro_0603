# TaskFlow

소규모 팀(≤5명)이 **칸반 + 실시간 채팅**으로 업무 진행을 한 화면에서 추적하는 MVP.

🔗 **배포**: https://taskflow-pro-0603-7amg.vercel.app · 📚 **API 문서(Swagger)**: [`/docs`](https://taskflow-pro-0603-7amg.vercel.app/docs)

---

## 주요 기능

- **인증** — 이메일+비밀번호 회원가입/로그인, JWT(24h, stateless), bcrypt 해시
- **팀** — 1인 1팀, `AAAA-9999` 초대코드로 합류, owner/member 2단계 권한
- **칸반** — TODO/DOING/DONE 3컬럼, 드래그로 상태 이동, 필터(전체/@me/미할당), assignee 지정
- **채팅** — `since_id` 기반 5초 증분 폴링(무손실), 1000자 제한, 본인 메시지 삭제
- **한국어 UI · KST(+09:00) 시간대** 고정

## 기술 스택

| 영역 | 스택 |
|------|------|
| 백엔드 | FastAPI · SQLAlchemy 2.0 · pydantic v2 · PyJWT · bcrypt |
| 프론트 | Vanilla JS (ES6 모듈) · Tailwind CSS (Play CDN) · 해시 라우터 SPA |
| DB | 로컬 SQLite ↔ 운영 Neon(PostgreSQL), `DATABASE_URL`로 전환 |
| 배포 | Vercel — `public/` 정적 + `api/index.py` Python 함수 |
| 테스트 | pytest + FastAPI TestClient (백엔드 51개) |

## 디렉토리 구조

```
taskflow_pro/
├── api/index.py          # Vercel Python 함수 진입점 (backend.app.main:app 노출)
├── vercel.json           # API 경로 → 함수 rewrite, 정적은 public/ 우선
├── requirements.txt      # Vercel 런타임 의존성 (psycopg[binary] 포함)
├── public/               # 프론트엔드 (정적 서빙)
│   ├── index.html
│   └── js/
│       ├── api.js        # fetch 래퍼 (JWT 자동 첨부, 401 redirect)
│       ├── router.js     # 해시 라우터 + 세션 가드
│       ├── store.js · layout.js · util.js
│       └── views/        # auth · teams · kanban · chat · members · forbidden
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI 앱, CORS, 에러 핸들러, 라우터 등록
│   │   ├── models.py     # 4테이블 (users/teams/tasks/messages)
│   │   ├── schemas.py    # pydantic 스키마 (KST 직렬화)
│   │   ├── core/         # config · db · security · errors · deps
│   │   └── routers/      # auth · teams · tasks · chat
│   ├── tests/            # pytest 51개 (conftest + 4 모듈)
│   └── requirements.txt  # 로컬 개발 의존성 (pytest 포함)
├── openspec/             # 스펙 (specs/ 메인 + changes/archive/)
└── docs/                 # 기획 PDF 2종
```

## 로컬 개발

### 백엔드

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

- Swagger UI: http://127.0.0.1:8000/docs · ReDoc: `/redoc` · 스키마: `/openapi.json`
- 기본 DB는 로컬 SQLite 파일(`sqlite:///./taskflow.db`). `DATABASE_URL` 환경변수로 Postgres 전환.

### 프론트엔드

```bash
cd public
python -m http.server 5500      # http://127.0.0.1:5500
```

`api.js`가 로컬이면 `http://127.0.0.1:8000`, 배포 환경이면 same-origin으로 자동 분기한다.

## 테스트

```bash
cd backend
.venv/Scripts/python.exe -m pytest        # 51 passed
```

테스트마다 격리된 in-memory SQLite(`get_db` 의존성 오버라이드)에서 실행되어 로컬/운영 DB에 영향이 없다. 18 API의 정상/에러/권한 케이스(비멤버 403, DELETE 권한 매트릭스, `since_id` 무손실, 1000자 초과, 중복 이메일, assignee 팀 한정)를 커버한다.

## API (18개)

| 그룹 | 엔드포인트 |
|------|-----------|
| **Auth** | `POST /auth/signup` · `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` |
| **Team** | `POST /teams` · `POST /teams/join` · `GET /teams/{id}` · `GET /teams/{id}/members` · `DELETE /teams/{id}/leave` |
| **Task** | `GET·POST /teams/{id}/tasks` · `GET·PUT·DELETE /tasks/{id}` · `PATCH /tasks/{id}/status` |
| **Chat** | `GET·POST /teams/{id}/messages` · `DELETE /messages/{id}` |

모든 4xx/5xx는 표준 형태로 반환한다:

```json
{ "error": { "code": "<SCREAMING_SNAKE>", "message": "<한국어 메시지>", "meta": {} } }
```

코드: `VALIDATION_ERROR` · `TOO_LONG` · `INVALID_CREDENTIALS` · `TOKEN_EXPIRED` · `FORBIDDEN` · `NOT_OWNER` · `NOT_FOUND` · `EMAIL_TAKEN` · `ALREADY_IN_TEAM` · `OWNER_CANNOT_LEAVE`

## 데이터 모델

- **users**: id · email(UNIQUE) · password_hash · team_id(FK→teams, NULL=미가입) · created_at
- **teams**: id · name(1–30자) · invite_code(UNIQUE, `AAAA-9999`) · owner_id(FK→users) · created_at
- **tasks**: id · team_id(FK, CASCADE) · title(1–100자) · status(`TODO|DOING|DONE`) · creator_id · assignee_id(FK, NULL) · created_at
- **messages**: id · team_id(FK, CASCADE) · user_id · content(1–1000자) · created_at

**규칙**: 1인 1팀(`users.team_id`) · '내 태스크' = `assignee_id` 기준 · 비멤버 `/teams/{id}/*` 접근 403 · DELETE task는 creator/owner · DELETE message는 본인만.

## 배포 (Vercel)

`main` 브랜치 push 시 자동 배포된다.

- `public/` 정적 파일이 먼저 서빙되고, `vercel.json` rewrite가 API 경로(`/auth/*`, `/teams/*`, `/tasks/*`, `/messages/*`, `/docs` 등)를 `api/index.py` 함수로 라우팅한다.
- DB는 Neon-Vercel 연동이 `DATABASE_URL`을 자동 주입한다. `JWT_SECRET`은 `vercel env`로 별도 설정한다.
- 비밀(DB 자격증명·JWT 시크릿)은 저장소에 커밋하지 않는다.

## 스펙

상세 명세는 `openspec/specs/`(메인 스펙 6종)와 `openspec/changes/archive/2026-06-05-taskflow-mvp/`(proposal·design·tasks)에 있다. 기획 원본은 `docs/`의 PDF 2종이며, 충돌 시 스토리보드 v2가 우선한다. 프로젝트 컨벤션·결정 8건은 [`CLAUDE.md`](./CLAUDE.md) 참조.

## 범위 외

알림 · 파일 첨부 · 전문 검색 · WebSocket(5초 폴링으로 대체) · 다국어 · JWT 갱신 토큰 · 팀 추방/역할 변경 · 관측성 도구.
