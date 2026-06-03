## ADDED Requirements

### Requirement: 팀 생성
시스템은 팀을 생성하면서 생성자를 owner로 지정하고 초대코드를 자동 발급해야 한다(SHALL). 초대코드는 정규식 `^[A-Z]{4}-[0-9]{4}$`를 따르며 UNIQUE이고 팀당 1개 고정·재발급 없음이다.

#### Scenario: 정상 생성
- **WHEN** 미소속 사용자가 1–30자 팀 이름으로 `POST /teams`
- **THEN** `teams` INSERT(owner_id=생성자), `users.team_id` UPDATE 후 201과 `{ id, name, invite_code, owner_id, created_at }`를 반환한다

#### Scenario: 초대코드 충돌 회피
- **WHEN** 생성한 초대코드가 기존 코드와 충돌
- **THEN** 새 코드를 재생성하여 UNIQUE를 보장한다

### Requirement: 초대코드 합류
시스템은 `user.team_id IS NULL`일 때만 초대코드로 팀에 합류시켜야 한다(SHALL). 한 사용자는 동시에 한 팀만 소속한다(1인 1팀).

#### Scenario: 정상 합류
- **WHEN** 미소속 사용자가 유효한 초대코드로 `POST /teams/join`
- **THEN** `users.team_id`를 해당 팀으로 UPDATE하고 200과 팀 정보·redirect를 반환한다

#### Scenario: 형식 오류
- **WHEN** 초대코드가 `AAAA-9999` 형식이 아님
- **THEN** 400 `VALIDATION_ERROR`를 반환한다

#### Scenario: 존재하지 않는 코드
- **WHEN** 형식은 맞으나 존재하지 않는 초대코드
- **THEN** 404 `NOT_FOUND`를 반환한다

#### Scenario: 이미 다른 팀 소속
- **WHEN** `team_id`가 이미 있는 사용자가 합류 시도
- **THEN** 409 `ALREADY_IN_TEAM`을 반환한다

### Requirement: 팀 정보 조회
시스템은 팀 멤버에게 팀 요약 정보를 반환해야 한다(SHALL).

#### Scenario: 멤버 조회
- **WHEN** 멤버가 `GET /teams/{id}` 호출
- **THEN** 200과 `{ id, name, invite_code, owner_id, owner_email, member_count, task_count, created_at }`를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 `GET /teams/{id}` 호출
- **THEN** 403 `FORBIDDEN`을 반환한다

### Requirement: 멤버 목록
시스템은 팀 멤버 목록을 owner/member 구분과 함께 반환해야 한다(SHALL).

#### Scenario: 멤버 목록 조회
- **WHEN** 멤버가 `GET /teams/{id}/members` 호출
- **THEN** 200과 각 멤버의 `{ id, email, role(owner|member), joined_at }`를 반환한다

### Requirement: 팀 떠나기
시스템은 멤버의 팀 탈퇴를 처리하되 owner 탈퇴는 제한해야 한다(SHALL). 소유권 위임은 범위 밖이다.

#### Scenario: 멤버 탈퇴
- **WHEN** member가 `DELETE /teams/{id}/leave` 호출
- **THEN** `users.team_id=NULL`로 UPDATE하고 팀은 유지된다

#### Scenario: 단독 owner 탈퇴
- **WHEN** 멤버가 자기뿐인 owner가 leave 호출
- **THEN** 팀과 연결된 tasks·messages를 CASCADE 삭제하고 owner의 `team_id=NULL`로 만든다

#### Scenario: 멤버가 남은 owner 탈퇴
- **WHEN** 다른 멤버가 남아 있는 owner가 leave 시도
- **THEN** 409 `OWNER_CANNOT_LEAVE`를 반환한다
