## Context

사전 설계 단계의 저장소. 두 기획 PDF + `CLAUDE.md`가 미션·페르소나·DB 4테이블·API 18개·권한·에러표준·비기능 요구사항을 확정했고, 충돌 시 스토리보드 v2(결정 8건)가 우선한다. 기술 스택은 사용자가 고정했다(FastAPI async / Vanilla JS + Tailwind / Vercel + Neon, SQLite 로컬). 라이브러리·디렉토리·마이그레이션·프론트 구조는 클로드코드 위임 영역이다.

이 문서는 propose 단계에서 확정한 **스펙 모순/공백 해소 8건**과, 사용자가 추가 지시한 **Swagger·자동 테스트 범위 확장**의 기술적 근거를 기록한다.

## Goals / Non-Goals

**Goals:**
- 18개 API·4테이블·9화면을 스펙 그대로 구현하고, 로컬 SQLite ↔ 운영 Neon을 `DATABASE_URL`로만 전환.
- 모든 에러를 `{ error: { code, message, meta } }`로 표준화하고, 권한(멤버십/소유권)을 미들웨어/의존성으로 일관 적용.
- `/docs`(Swagger UI)를 태그·response model·에러 스키마로 주석화해 18개 API를 수동 테스트 가능하게 함.
- pytest + TestClient로 정상/에러/권한 케이스 회귀 테스트 가능하게 함.

**Non-Goals:**
- 알림·파일첨부·전문검색·다국어·WebSocket·JWT 갱신토큰·추방/역할변경·관측성 도구(범위 외 유지).
- 칸반 컬럼 내 수동 정렬, 소유권 위임(아래 결정 #6·#3에서 명시 제외).
- 프론트엔드 자동 테스트(이번 테스트 범위는 백엔드 pytest로 한정; E2E는 추후 Playwright 옵션).

## Decisions

### D1. 타임스탬프 = KST(+09:00) timezone-aware (스펙 모순 해소 ①)
도메인 규칙 "KST·UTC 변환 없음"과 JSON 예시의 `Z`(UTC)가 충돌. **timezone-aware datetime을 KST(+09:00)로 저장·직렬화하고 `Z` 대신 `+09:00` offset을 반환.** Vercel/Neon이 UTC 기반이어도 offset이 명시되어 모호함 없음.
- 대안: (a) UTC 저장 + 프론트 변환 — "변환 없음" 의도와 어긋남. (b) naive datetime — 서버리스 UTC 환경에서 9시간 어긋나는 버그 위험. → 기각.

### D2. 채팅 폴링 커서 = id 기반 `since_id` (스펙 모순 해소 ②)
"메시지 누락 0건"은 critical metric. created_at 기반 커서는 동일 초 다건에서 경계 누락/중복 발생. **`GET /teams/{id}/messages?since_id=<마지막 id>` → `WHERE team_id=? AND id > since_id ORDER BY id ASC`.** auto-increment id는 단조 증가라 무손실. `since_id` 없으면 최근 50개(`ORDER BY id DESC LIMIT 50` 후 역순). 응답에 각 메시지 `id` 포함.
- 대안: `(created_at, id)` 복합 커서 — 정확하나 파라미터 2개로 복잡. id 단독으로 충분.

### D3. owner leave 및 팀 수명주기 (공백 해소 ③)
`teams.owner_id` NOT NULL + 위임 범위 밖. **member leave → `team_id=NULL`(팀 유지). owner leave → 멤버가 자기뿐일 때만 허용, 팀과 tasks/messages를 FK CASCADE로 삭제. 다른 멤버가 남아 있으면 409 `OWNER_CANNOT_LEAVE`.** member는 항상 owner와 공존하므로 "고아 팀"이 발생하지 않음.
- 대안: 소유권 자동 위임 — 결정상 범위 밖. owner leave 시 즉시 팀 전체 삭제 — 잔존 멤버 데이터 손실로 기각.

### D4. 합류 선행조건 + `ALREADY_IN_TEAM` 신설 (공백 해소 ④)
`POST /teams/join`은 `user.team_id IS NULL`일 때만. 이미 소속이면 409 `ALREADY_IN_TEAM`. 1인 1팀(결정 #1) 불변식 보호. 표준 에러표에 코드 1건 추가.

### D5. assignee = 같은 팀 멤버 한정 (공백 해소 ⑤)
`tasks.assignee_id`는 NULL이거나 `users.team_id == task.team_id`인 사용자만. 위반 시 400 `VALIDATION_ERROR`. POST/PUT 양쪽에서 검증해 비멤버 배정 누수 차단.

### D6. 컬럼 내 수동정렬 미지원 (공백 해소 ⑥)
`tasks`에 position 컬럼 없음. 정렬은 `created_at DESC` 고정, 드래그는 `PATCH /tasks/{id}/status`(컬럼 이동)만 영속화. 컬럼 내 순서 변경은 비영속(새로고침 시 created_at 순).

### D7. `GET /teams/{id}` 응답 형태 (공백 해소 ⑦)
`{ id, name, invite_code, owner_id, owner_email, member_count, task_count, created_at }`. C·03 미리보기(멤버수·태스크수·owner) 충족. 멤버만 접근(비멤버 403)이라 invite_code 노출 안전.

### D8. CORS 허용목록 (공백 해소 ⑧)
env `CORS_ORIGINS`(콤마 구분) 허용목록. 기본값 `http://localhost:*` + `https://taskflow.vercel.app`. Vercel 프리뷰(`*.vercel.app`)는 옵션 정규식으로 토글.

### D9. 권한 적용 패턴
FastAPI 의존성으로 계층화: `get_current_user`(JWT 검증·만료→401 `TOKEN_EXPIRED`) → `require_team_member(team_id)`(멤버십→비멤버 403 `FORBIDDEN`) → 리소스별 소유권 체크(DELETE task creator/owner, DELETE message 본인→403 `NOT_OWNER`). 라우트 시그니처에서 권한이 드러나게.

### D10. 에러 표준화 = 전역 예외 핸들러
도메인 `AppError(code, message, status, meta)` + FastAPI `exception_handler`로 `{error:{code,message,meta}}` 일관 직렬화. pydantic `RequestValidationError`도 `VALIDATION_ERROR`로 매핑. 민감정보(이메일 존재 여부) 비노출 — 로그인 실패는 항상 동일 `INVALID_CREDENTIALS`.

### D11. Swagger/OpenAPI (사용자 지시)
FastAPI 자동 OpenAPI 활용 — 추가 패키지 불필요. 라우트에 `tags`(Auth/Team/Task/Chat), `response_model`(pydantic), 표준 에러 응답 예시를 부여해 `/docs`를 실사용 테스트 콘솔로. Bearer 토큰 인증 스킴 등록해 `/docs`에서 Authorize 후 호출 가능하게.

### D12. 테스트 전략 = pytest + TestClient (결정 #7 override)
`pytest` + FastAPI `TestClient`(httpx) + 격리된 임시 SQLite(또는 in-memory)로 18개 API의 정상/에러/권한 케이스. fixture로 사용자·팀·JWT 생성. 핵심 회귀: 비멤버 403 격리, DELETE 권한 매트릭스, 채팅 `since_id` 무손실, 1000자 초과 400, 중복 이메일 409, assignee 팀 한정.

### D13. 환경 분리 / 배포
`DATABASE_URL`로 `sqlite:///./taskflow.db` ↔ `postgres://...neon`. SQLAlchemy로 양쪽 호환. Vercel: 프론트 정적 + 백엔드 ASGI를 Serverless Functions로(엔트리 `api/`). 라이브러리·마이그레이션 도구·프론트 SPA/MPA·CSS 빌드는 구현 시 확정(위임).

## Risks / Trade-offs

- **서버리스 + SQLite 비영속** → 운영은 Neon만 사용, SQLite는 로컬 전용으로 한정. `DATABASE_URL` 미설정 시 로컬 기본값.
- **서버리스 콜드스타트로 API 100ms 기준 초과 가능** → 정성 검증(결정 #7), 커넥션 풀(Neon pooled URL) 사용으로 완화.
- **5초 폴링 부하**(팀당 ≤5명·≤50동접 가정) → `messages(team_id, id)` 인덱스 + `since_id` 증분으로 페이로드 최소화.
- **invite_code 충돌**(26^4·10^4 공간) → INSERT UNIQUE 충돌 시 재생성 재시도.
- **KST offset 저장**이 향후 다지역 확장과 충돌 → 범위 외(단일 시간대 가정)로 수용.
- **결정 #7 override가 스펙과 불일치** → proposal/`CLAUDE.md`에 명시 기록해 추적.

## Open Questions

- Vercel 운영 도메인 최종 확정값(`taskflow.vercel.app` 가정) 및 프리뷰 URL 허용 여부 — 배포 단계에서 `CORS_ORIGINS`로 확정.
- 마이그레이션 도구 채택(Alembic vs 부팅 시 create_all) — 구현 착수 시 결정(MVP는 create_all로 충분할 수 있음).
