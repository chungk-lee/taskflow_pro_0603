# task-board Specification

## Purpose

칸반 보드. 팀 범위 태스크 조회·필터(전체/@me/미할당)·생성·상세·수정·상태 이동(드래그)·삭제를 담당하며 '내 태스크'는 assignee 기준이다.

## Requirements

### Requirement: 칸반 조회 및 필터
시스템은 팀 멤버에게 태스크를 `created_at DESC`로 반환하고 필터(전체/@me/미할당)를 지원해야 한다(SHALL). '내 태스크'는 `assignee_id = current_user_id` 기준이며 creator 기준이 아니다.

#### Scenario: 전체 조회
- **WHEN** 멤버가 `GET /teams/{id}/tasks` (filter 없음)
- **THEN** 200과 해당 팀의 모든 태스크를 `created_at DESC`로 반환한다

#### Scenario: @me 필터
- **WHEN** filter=@me로 조회
- **THEN** `assignee_id = current_user_id`인 태스크만 반환한다

#### Scenario: 미할당 필터
- **WHEN** filter=미할당으로 조회
- **THEN** `assignee_id IS NULL`인 태스크만 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 조회
- **THEN** 403 `FORBIDDEN`을 반환한다

### Requirement: 태스크 생성
시스템은 멤버가 태스크를 생성하도록 허용해야 한다(SHALL). title은 1–100자, 기본 status는 TODO, creator는 현재 사용자다.

#### Scenario: 정상 생성
- **WHEN** 멤버가 1–100자 title(및 선택 assignee)로 `POST /teams/{id}/tasks`
- **THEN** 201과 생성된 태스크를 반환한다(creator_id=현재 사용자, created_at 기록)

#### Scenario: 제목 길이 오류
- **WHEN** title이 비었거나 100자 초과
- **THEN** 400 `VALIDATION_ERROR`를 반환한다

### Requirement: assignee 팀 멤버 한정
시스템은 `assignee_id`를 NULL이거나 같은 팀 멤버로만 허용해야 한다(SHALL).

#### Scenario: 팀 멤버 배정
- **WHEN** 같은 팀 멤버를 assignee로 지정
- **THEN** 정상 저장한다

#### Scenario: 비멤버 배정 차단
- **WHEN** 다른 팀 사용자 또는 미가입 사용자를 assignee로 지정
- **THEN** 400 `VALIDATION_ERROR`를 반환한다

### Requirement: 태스크 상세 조회
시스템은 멤버에게 단일 태스크 상세를 반환해야 한다(SHALL).

#### Scenario: 상세 조회
- **WHEN** 멤버가 `GET /tasks/{id}` 호출
- **THEN** 200과 `{ id, title, status, creator_id, assignee_id, created_at }`를 반환한다

### Requirement: 제목·담당자 수정
시스템은 멤버가 태스크의 title과 assignee를 수정하도록 허용해야 한다(SHALL). status는 이 엔드포인트로 변경하지 않는다.

#### Scenario: 수정 성공
- **WHEN** 멤버가 `PUT /tasks/{id}`로 title/assignee 수정
- **THEN** 200과 갱신된 태스크를 반환한다(assignee는 팀 멤버 한정 검증)

### Requirement: 상태 이동(드래그 전용)
시스템은 status 이동을 `PATCH /tasks/{id}/status` 전용 엔드포인트로 처리해야 한다(SHALL). status는 `TODO|DOING|DONE`만 허용한다. 컬럼 내 수동 정렬은 영속화하지 않는다.

#### Scenario: 상태 변경
- **WHEN** 멤버가 `PATCH /tasks/{id}/status { status: "DOING" }`
- **THEN** 200과 status가 갱신된 태스크를 반환한다

#### Scenario: 잘못된 상태값
- **WHEN** status가 허용 enum 밖
- **THEN** 400 `VALIDATION_ERROR`를 반환한다

### Requirement: 태스크 삭제 권한
시스템은 creator 또는 team owner만 태스크를 삭제하도록 허용해야 한다(SHALL). owner는 타인 카드도 삭제 가능(오버라이드), member는 본인 카드만.

#### Scenario: creator 삭제
- **WHEN** 카드 생성자가 `DELETE /tasks/{id}`
- **THEN** 200으로 삭제한다

#### Scenario: owner 오버라이드 삭제
- **WHEN** team owner가 타인 카드 삭제
- **THEN** 200으로 삭제한다

#### Scenario: 권한 없는 삭제
- **WHEN** creator도 owner도 아닌 member가 타인 카드 삭제 시도
- **THEN** 403 `FORBIDDEN`을 반환한다
