# platform-foundation Specification

## Purpose

백엔드 횡단 기반. 표준 에러 응답, JWT·멤버십 권한, OpenAPI/Swagger 문서, CORS, 데이터 모델/인덱스, 환경 분리·배포, 백엔드 자동 테스트를 담당한다.

## Requirements

### Requirement: 표준 에러 응답
시스템은 모든 4xx/5xx 응답을 `{ error: { code, message, meta } }` 형태로 반환해야 한다(SHALL). `code`는 SCREAMING_SNAKE, `message`는 한국어, `meta`는 옵션이다. 민감정보(이메일 존재 여부 등)는 노출하지 않는다(MUST NOT).

#### Scenario: 일관된 에러 형태
- **WHEN** 임의의 핸들러가 도메인 오류를 발생
- **THEN** 동일한 `{ error: { code, message, meta } }` JSON으로 직렬화된다

#### Scenario: 검증 오류 매핑
- **WHEN** pydantic 요청 검증이 실패
- **THEN** 400 `VALIDATION_ERROR`로 변환되어 표준 형태로 반환된다

#### Scenario: 에러 코드 집합
- **WHEN** 각 오류 상황이 발생
- **THEN** 코드는 `VALIDATION_ERROR`, `TOO_LONG`, `INVALID_CREDENTIALS`, `TOKEN_EXPIRED`, `FORBIDDEN`, `NOT_OWNER`, `NOT_FOUND`, `EMAIL_TAKEN`, `ALREADY_IN_TEAM`, `OWNER_CANNOT_LEAVE` 중 하나다

### Requirement: JWT 및 멤버십 권한
시스템은 JWT 검증과 팀 멤버십을 의존성으로 적용해야 한다(SHALL). 모든 `/teams/*` 라우트는 `user.team_id == {id}`를 확인하고 비멤버는 읽기·쓰기 모두 403이다.

#### Scenario: 만료 토큰
- **WHEN** 만료/누락 토큰으로 보호된 엔드포인트 접근
- **THEN** 401 `TOKEN_EXPIRED`를 반환한다

#### Scenario: 비멤버 격리
- **WHEN** team=1 사용자가 `GET /teams/2/*` 접근
- **THEN** 403 `FORBIDDEN`을 반환한다(권한 격리 100%)

### Requirement: OpenAPI/Swagger 문서
시스템은 18개 API를 태그·response model·표준 에러 스키마로 문서화하고 `/docs`(Swagger UI)와 `/redoc`을 제공해야 한다(SHALL). Bearer 인증 스킴을 등록해 `/docs`에서 인증 후 호출할 수 있어야 한다.

#### Scenario: Swagger UI 접근
- **WHEN** 개발자가 `/docs` 접속
- **THEN** Auth/Team/Task/Chat 태그로 그룹된 18개 엔드포인트와 요청/응답 스키마가 표시된다

#### Scenario: 인증 후 호출
- **WHEN** `/docs`에서 Bearer 토큰으로 Authorize 후 보호된 API 실행
- **THEN** 인증 헤더가 첨부되어 정상 응답을 받는다

### Requirement: CORS 허용목록
시스템은 환경변수 `CORS_ORIGINS` 기반 허용목록으로 CORS를 제어해야 한다(SHALL). 기본값은 `localhost`와 운영 도메인이다.

#### Scenario: 허용 출처
- **WHEN** 허용목록에 포함된 출처에서 요청
- **THEN** CORS 헤더를 허용한다

#### Scenario: 비허용 출처
- **WHEN** 허용목록에 없는 출처에서 요청
- **THEN** CORS를 허용하지 않는다

### Requirement: 데이터 모델 및 인덱스
시스템은 4테이블(users/teams/tasks/messages)과 핵심 인덱스를 구현해야 한다(SHALL). `users.team_id`(nullable, 1인 1팀), `tasks.assignee_id`(nullable), `tasks.created_at`(정렬)을 포함한다.

#### Scenario: 인덱스 존재
- **WHEN** 스키마를 생성
- **THEN** `tasks(team_id, created_at)`, `messages(team_id, id)`, `teams(invite_code)` UNIQUE, `users.team_id` 인덱스가 존재한다

#### Scenario: FK CASCADE
- **WHEN** 팀이 삭제됨(단독 owner leave)
- **THEN** 연결된 tasks·messages가 CASCADE 삭제된다

### Requirement: 환경 분리 및 배포
시스템은 `DATABASE_URL`만으로 로컬 SQLite ↔ 운영 Neon을 전환해야 한다(SHALL). 운영은 Vercel(정적 프론트 + Serverless Functions)에 `main` push로 자동 배포한다. 로컬 SQLite 파일은 git에서 제외한다.

#### Scenario: 로컬 실행
- **WHEN** `DATABASE_URL`이 SQLite를 가리킴
- **THEN** `uvicorn`으로 로컬 SQLite에 연결되어 동작한다

#### Scenario: 운영 전환
- **WHEN** `DATABASE_URL`이 Neon Postgres를 가리킴
- **THEN** 코드 변경 없이 Neon에 연결된다

### Requirement: 백엔드 자동 테스트
시스템은 pytest + FastAPI TestClient로 18개 API의 정상/에러/권한 케이스 회귀 테스트를 제공해야 한다(SHALL). 결정 #7(테스트 자동화 범위 외)을 사용자 지시로 override한다.

#### Scenario: 테스트 실행
- **WHEN** `pytest`를 실행
- **THEN** 격리된 임시 DB로 모든 테스트가 독립 실행된다

#### Scenario: 핵심 회귀 커버리지
- **WHEN** 테스트 스위트를 수행
- **THEN** 비멤버 403 격리, DELETE 권한 매트릭스, 채팅 `since_id` 무손실, 1000자 초과 400, 중복 이메일 409, assignee 팀 한정을 검증한다
