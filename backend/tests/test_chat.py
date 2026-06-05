"""Chat API (3): send / poll(since_id) / delete + 권한·길이 규칙."""


def _send(client, headers, team_id, content="안녕하세요"):
    r = client.post(f"/teams/{team_id}/messages", json={"content": content}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_send_message(client, make_team):
    acc, team = make_team()
    msg = _send(client, acc["headers"], team["id"], "첫 메시지")
    assert msg["content"] == "첫 메시지"
    assert msg["user_id"] == acc["user"]["id"]
    assert msg["user_email"] == "owner@ex.com"
    assert "created_at" in msg


def test_send_empty_content_400(client, make_team):
    acc, team = make_team()
    r = client.post(f"/teams/{team['id']}/messages", json={"content": ""}, headers=acc["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_send_too_long_400(client, make_team):
    acc, team = make_team()
    r = client.post(f"/teams/{team['id']}/messages", json={"content": "a" * 1001}, headers=acc["headers"])
    assert r.status_code == 400
    body = r.json()["error"]
    assert body["code"] == "TOO_LONG"
    assert body["meta"]["limit"] == 1000
    assert body["meta"]["actual"] == 1001


def test_send_nonmember_403(client, make_team, register):
    _, team = make_team()
    outsider = register("out@ex.com")
    r = client.post(f"/teams/{team['id']}/messages", json={"content": "x"}, headers=outsider["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_list_initial_chronological(client, make_team):
    acc, team = make_team()
    _send(client, acc["headers"], team["id"], "1")
    _send(client, acc["headers"], team["id"], "2")
    _send(client, acc["headers"], team["id"], "3")
    msgs = client.get(f"/teams/{team['id']}/messages", headers=acc["headers"]).json()
    assert [m["content"] for m in msgs] == ["1", "2", "3"]  # 시간순(오름차순)


def test_list_since_id_increment(client, make_team):
    acc, team = make_team()
    m1 = _send(client, acc["headers"], team["id"], "1")
    _send(client, acc["headers"], team["id"], "2")
    msgs = client.get(
        f"/teams/{team['id']}/messages?since_id={m1['id']}", headers=acc["headers"]
    ).json()
    assert [m["content"] for m in msgs] == ["2"]  # m1 이후만


def test_list_since_id_empty_when_no_new(client, make_team):
    acc, team = make_team()
    m1 = _send(client, acc["headers"], team["id"], "1")
    msgs = client.get(
        f"/teams/{team['id']}/messages?since_id={m1['id']}", headers=acc["headers"]
    ).json()
    assert msgs == []


def test_delete_own_message(client, make_team):
    acc, team = make_team()
    msg = _send(client, acc["headers"], team["id"])
    r = client.delete(f"/messages/{msg['id']}", headers=acc["headers"])
    assert r.status_code == 200
    # 삭제 확인
    msgs = client.get(f"/teams/{team['id']}/messages", headers=acc["headers"]).json()
    assert msgs == []


def test_delete_others_message_403_not_owner(client, make_team, join_member):
    """owner라도 타인 메시지는 삭제 불가 → NOT_OWNER."""
    owner, team = make_team()
    member = join_member(team["invite_code"], "m@ex.com")
    msg = _send(client, member["headers"], team["id"], "멤버 메시지")
    r = client.delete(f"/messages/{msg['id']}", headers=owner["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "NOT_OWNER"


def test_delete_message_nonmember_403_forbidden(client, make_team, register):
    owner, team = make_team()
    msg = _send(client, owner["headers"], team["id"])
    outsider = register("out@ex.com")
    r = client.delete(f"/messages/{msg['id']}", headers=outsider["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_poll_nonmember_403(client, make_team, register):
    _, team = make_team()
    outsider = register("out@ex.com")
    r = client.get(f"/teams/{team['id']}/messages", headers=outsider["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"
