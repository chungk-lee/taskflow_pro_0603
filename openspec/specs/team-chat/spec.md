# team-chat Specification

## Purpose

팀 실시간 채팅. 1–1000자 메시지 전송, `since_id` 기반 무손실 증분 폴링, 본인 메시지 삭제를 담당한다.

## Requirements

### Requirement: 메시지 전송
시스템은 팀 멤버가 1–1000자 메시지를 전송하도록 허용해야 한다(SHALL). 길이는 클라이언트와 서버 양쪽에서 검증한다.

#### Scenario: 정상 전송
- **WHEN** 멤버가 1–1000자 content로 `POST /teams/{id}/messages`
- **THEN** 201과 `{ id, user_id, user_email, content, created_at }`를 반환한다

#### Scenario: 1000자 초과
- **WHEN** content가 1000자 초과
- **THEN** 400 `{ error: { code: "TOO_LONG", meta: { limit: 1000, actual } } }`를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 전송 시도
- **THEN** 403 `FORBIDDEN`을 반환한다

### Requirement: 증분 폴링 수신
시스템은 `since_id` 기반 증분 폴링으로 메시지를 반환해야 하며, POST로 성공(201)한 메시지는 이후 모든 GET에서 누락 없이 노출되어야 한다(SHALL, 메시지 누락 0건).

#### Scenario: 최초 조회
- **WHEN** `since_id` 없이 `GET /teams/{id}/messages`
- **THEN** 최근 50개를 시간순으로 반환하고 각 메시지의 `id`를 포함한다

#### Scenario: 증분 조회
- **WHEN** `GET /teams/{id}/messages?since_id=<마지막 id>`
- **THEN** `id > since_id`인 메시지만 `id ASC`로 반환한다(동일 시각 다건도 무손실)

#### Scenario: 새 메시지 없음
- **WHEN** `since_id` 이후 새 메시지가 없음
- **THEN** 200과 빈 배열을 반환한다

### Requirement: 메시지 삭제(본인만)
시스템은 본인 메시지만 삭제하도록 허용해야 한다(SHALL). owner라도 타인 메시지는 삭제할 수 없다(MUST NOT).

#### Scenario: 본인 메시지 삭제
- **WHEN** 작성자가 `DELETE /messages/{id}`
- **THEN** 200으로 삭제한다

#### Scenario: 타인 메시지 삭제 차단
- **WHEN** owner를 포함한 타인이 남의 메시지 삭제 시도
- **THEN** 403 `NOT_OWNER`를 반환한다
