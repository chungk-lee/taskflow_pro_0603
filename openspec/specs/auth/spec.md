# auth Specification

## Purpose

이메일+비밀번호 기반 인증. JWT(24h, stateless logout) 발급/검증과 로그인 후 `team_id` 기반 진입 분기를 담당한다.

## Requirements

### Requirement: 회원가입
시스템은 이메일과 비밀번호로 신규 계정을 생성하고 즉시 JWT를 발급해야 한다(SHALL). 비밀번호는 bcrypt로 해시하여 저장하고 평문은 절대 저장하지 않는다(MUST NOT). 이메일 인증 단계는 없다.

#### Scenario: 정상 회원가입
- **WHEN** 유효한 이메일과 8자 이상 비밀번호로 `POST /auth/signup` 호출
- **THEN** `users`에 `team_id=NULL`로 INSERT하고 201과 JWT(exp 24h)를 반환한다

#### Scenario: 중복 이메일
- **WHEN** 이미 가입된 이메일로 회원가입
- **THEN** 409 `{ error: { code: "EMAIL_TAKEN" } }`를 반환한다

#### Scenario: 형식 오류
- **WHEN** 이메일 형식이 잘못되었거나 비밀번호가 8자 미만
- **THEN** 400 `VALIDATION_ERROR`를 반환한다(서버측 재검증)

### Requirement: 로그인
시스템은 자격 증명을 검증하고 성공 시 JWT(exp 24h)를 반환해야 한다(SHALL). 실패 시 이메일 존재 여부를 노출하지 않고 동일한 메시지를 반환한다(MUST NOT 노출).

#### Scenario: 로그인 성공
- **WHEN** 올바른 이메일·비밀번호로 `POST /auth/login`
- **THEN** 200과 `{ token, user: { id, email, team_id } }`를 반환한다

#### Scenario: 자격 증명 실패
- **WHEN** 존재하지 않는 이메일 또는 틀린 비밀번호로 로그인
- **THEN** 두 경우 모두 401 `INVALID_CREDENTIALS`와 동일 메시지를 반환한다

### Requirement: 로그아웃(stateless)
시스템은 서버 측 토큰 블랙리스트를 유지하지 않아야 한다(MUST NOT). 로그아웃은 200만 반환하고 토큰 폐기는 클라이언트가 수행한다.

#### Scenario: 로그아웃 호출
- **WHEN** `POST /auth/logout` 호출
- **THEN** 200을 반환하고 서버 상태는 변경하지 않는다

### Requirement: 현재 사용자 조회
시스템은 유효한 JWT로 현재 사용자 정보를 반환해야 한다(SHALL).

#### Scenario: 유효한 토큰
- **WHEN** 유효한 Bearer 토큰으로 `GET /auth/me`
- **THEN** 200과 `{ id, email, team_id }`를 반환한다

#### Scenario: 만료/누락 토큰
- **WHEN** 토큰이 만료되었거나 없는 상태로 인증 필요 엔드포인트 호출
- **THEN** 401 `TOKEN_EXPIRED`를 반환한다

### Requirement: 로그인 후 분기
시스템은 로그인 후 `team_id`에 따라 진입 화면을 분기해야 한다(SHALL).

#### Scenario: 미가입 사용자
- **WHEN** `team_id == NULL`인 사용자가 로그인
- **THEN** 팀 선택 화면으로 강제 이동한다

#### Scenario: 소속 사용자
- **WHEN** `team_id`가 있는 사용자가 로그인
- **THEN** `/teams/{team_id}` 칸반으로 이동한다
