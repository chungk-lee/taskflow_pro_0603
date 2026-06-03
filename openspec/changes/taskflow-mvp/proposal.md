## Why

TaskFlow는 소규모 팀(≤5명)이 칸반과 실시간 채팅을 한 화면에서 추적하도록 돕는 MVP다. 저장소는 두 기획 문서(`docs/TaskFlow_프로그램정의.pdf`, `docs/TaskFlow_스토리보드.pdf`)와 `CLAUDE.md`로 스펙이 완성된 사전 설계 단계이며, 아직 코드가 없다. 이 변경은 그 스펙을 실행 가능한 백엔드·프론트엔드·배포로 구현한다. 충돌 시 스토리보드 v2(통합본 결정 8건)가 우선한다.

## What Changes

- **백엔드(FastAPI, async)**: API 18개(Auth 4 + Team 5 + Task 6 + Chat 3), DB 4테이블(users/teams/tasks/messages), JWT 인증(24h, stateless logout), bcrypt 비밀번호 해시.
- **권한 모델**: 모든 `/teams/*`는 JWT + 멤버십(`user.team_id == {id}`) 검증, 비멤버 403. DELETE task는 creator/owner, DELETE message는 본인만.
- **표준 에러 응답**: 모든 4xx/5xx를 `{ error: { code, message, meta } }`로 통일.
- **프론트엔드(Vanilla JS + Tailwind)**: 9개 화면(로그인·회원가입·팀선택·팀생성·칸반·카드모달·채팅·멤버·403), JWT localStorage 관리, 칸반 드래그, 채팅 5초 폴링(모바일 포커스 2초), 반응형.
- **배포**: 로컬 SQLite ↔ 운영 Neon을 `DATABASE_URL`로 전환, Vercel(정적 프론트 + Serverless Functions), `main` push 자동 배포.
- **스펙 모순/공백 해소 8건 확정**: 타임스탬프 KST(+09:00), 채팅 커서 id 기반(`since_id`), owner leave 규칙, `ALREADY_IN_TEAM` 코드 신설, assignee는 팀 멤버 한정, 컬럼 내 수동정렬 미지원, `GET /teams/{id}` 응답 형태, CORS 허용목록. (design.md에 근거 기록)
- **BREAKING (스펙 대비)**: 통합본 결정 #7 "테스트 자동화 범위 외"를 **사용자 지시로 override** → 백엔드 pytest 자동 테스트 스위트를 산출물에 포함. Swagger UI(`/docs`)·ReDoc(`/redoc`)를 태그·response model·표준 에러 스키마로 주석화해 API 테스트 콘솔로 제공.

## Capabilities

### New Capabilities
- `auth`: 회원가입·로그인·로그아웃·현재 사용자 조회. JWT(24h) 발급/검증, bcrypt 해시, `INVALID_CREDENTIALS`/`TOKEN_EXPIRED`/`EMAIL_TAKEN` 처리, 로그인 후 team_id 분기.
- `team-management`: 팀 생성(invite_code 자동 발급)·합류·조회·멤버 목록·떠나기. 1인 1팀, owner/member 권한, owner leave 및 중복 소속 규칙.
- `task-board`: 칸반 태스크 생성·조회(필터 전체/@me/미할당)·상세·제목+assignee 수정·상태 이동(드래그)·삭제. assignee 팀 멤버 한정, creator/owner 삭제 권한.
- `team-chat`: 팀 채팅 송신·증분 폴링 수신(`since_id`)·삭제(본인만). 1000자 검증, 메시지 누락 0건 보장.
- `platform-foundation`: 표준 에러 응답, JWT·멤버십 권한 미들웨어, OpenAPI/Swagger 문서화, CORS 허용목록, DB 4테이블+인덱스, `DATABASE_URL` 환경 분리, Vercel 배포, pytest 백엔드 테스트 스위트.
- `web-frontend`: 9개 화면(Vanilla JS + Tailwind), fetch 기반 API 연동·JWT localStorage·401 redirect, 칸반 드래그, 채팅 폴링, 반응형(모바일 햄버거/스와이프).

### Modified Capabilities
<!-- 기존 스펙 없음 (openspec/specs/ 비어 있음). 해당 없음. -->

## Impact

- **신규 코드**: 백엔드 FastAPI 앱(라우터 18개·모델 4개·인증/권한·에러 핸들러), 프론트 정적 자산(9화면), pytest 테스트, Vercel 설정(`vercel.json`).
- **의존성(클로드코드 위임)**: SQLAlchemy/pydantic/bcrypt(passlib)/python-jose, pytest/httpx, 마이그레이션 도구 등 design.md에서 확정.
- **환경/시크릿**: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`. 로컬 SQLite 파일은 git 제외.
- **배포 파이프라인**: GitHub `main` → Vercel(프론트 정적 + 백엔드 Serverless) + Neon.
- **스펙 변경**: 결정 #7 override(테스트 자동화 포함)에 맞춰 추후 `CLAUDE.md`의 "범위 외"·개발 섹션 갱신 필요.
