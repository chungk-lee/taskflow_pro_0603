# web-frontend Specification

## Purpose

Vanilla JS(ES6+) + Tailwind SPA. 9개 화면, JWT 세션 관리, 칸반 드래그, 클라이언트 검증, 채팅 폴링, 반응형 레이아웃을 담당한다.

## Requirements

### Requirement: 화면 구성
시스템은 Vanilla JS(ES6+) + Tailwind로 9개 화면을 구현해야 한다(SHALL): 로그인, 회원가입, 팀 선택(미가입), 팀 생성/초대코드, 칸반, 카드 상세/수정 모달, 채팅, 멤버 목록, 403. UI는 한국어만이다.

#### Scenario: 화면 렌더링
- **WHEN** 각 경로에 진입
- **THEN** 해당 화면이 기획 와이어프레임대로 렌더링된다(초기/입력/처리/에러 상태 포함)

#### Scenario: empty state
- **WHEN** 태스크 0건 또는 메시지 0건
- **THEN** 칸반/채팅이 첫 작성 유도 empty state를 표시한다

### Requirement: 인증 세션 관리
프론트엔드는 JWT를 localStorage에 저장·읽기·삭제하고 401 시 토큰 삭제 후 `/login`으로 redirect해야 한다(SHALL). 직전 URL은 저장하지 않는다.

#### Scenario: 로그인 저장 및 분기
- **WHEN** 로그인 성공
- **THEN** 토큰을 저장하고 `team_id` 유무에 따라 팀 선택 또는 칸반으로 이동한다

#### Scenario: 401 자동 redirect
- **WHEN** 임의 API가 401 반환
- **THEN** 토큰을 삭제하고 `/login`으로 이동한다

#### Scenario: 미가입 보호
- **WHEN** `team_id=NULL` 사용자가 `/teams/*` 직접 접근
- **THEN** 팀 선택 화면으로 돌려보낸다

### Requirement: 칸반 드래그 앤 드롭
프론트엔드는 HTML5 드래그로 카드를 컬럼 간 이동하고 drop 시 `PATCH /tasks/{id}/status`를 호출해야 한다(SHALL).

#### Scenario: 컬럼 이동
- **WHEN** 카드를 다른 컬럼에 drop
- **THEN** 대상 컬럼 highlight 후 status PATCH를 호출하고 새 위치를 확정한다(반응 < 50ms 정성 목표)

### Requirement: 클라이언트 검증
프론트엔드는 1차 검증을 수행해야 한다(SHALL): 이메일 형식, 비밀번호 8자 이상, 초대코드 `AAAA-9999`, 메시지 1000자 카운터.

#### Scenario: 메시지 카운터
- **WHEN** 입력이 1000자를 초과
- **THEN** 카운터를 적색 표시하고 전송 버튼을 비활성화한다

### Requirement: 채팅 폴링
프론트엔드는 `since_id` 기반 5초 폴링(모바일 입력 포커스 시 2초)으로 새 메시지를 증분 수신해야 한다(SHALL).

#### Scenario: 증분 폴링
- **WHEN** 채팅 화면이 활성
- **THEN** 5초마다 마지막 수신 id로 `?since_id=`를 호출하고 새 메시지만 추가한다

#### Scenario: 폴링 실패
- **WHEN** 폴링 요청이 네트워크 실패
- **THEN** 연결 끊김 표시 후 재시도(backoff)하고 복구 시 `since_id`로 누락분을 일괄 수신한다

### Requirement: 반응형 레이아웃
프론트엔드는 Tailwind breakpoint로 반응형을 제공해야 한다(SHALL): <768px 모바일(햄버거 메뉴, 칸반 컬럼 스와이프, 풀스크린 채팅), 데스크탑 3컬럼.

#### Scenario: 모바일 칸반
- **WHEN** 화면 폭 <768px
- **THEN** 칸반이 1컬럼 스와이프 모드로 전환되고 동일 API를 사용한다
