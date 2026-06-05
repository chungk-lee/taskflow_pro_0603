"""Team API (5): create / join / get / members / leave + 권한·1인1팀 규칙."""
import re


def test_create_team(client, register):
    acc = register("owner@ex.com")
    r = client.post("/teams", json={"name": "프론티어스"}, headers=acc["headers"])
    assert r.status_code == 201
    team = r.json()
    assert team["name"] == "프론티어스"
    assert re.fullmatch(r"[A-Z]{4}-[0-9]{4}", team["invite_code"])  # AAAA-9999 형식
    assert team["owner_id"] == acc["user"]["id"]
    assert team["member_count"] == 1
    assert team["task_count"] == 0


def test_create_team_when_already_in_team_409(client, make_team):
    acc, _ = make_team()
    r = client.post("/teams", json={"name": "두번째팀"}, headers=acc["headers"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_IN_TEAM"


def test_create_team_name_too_long_400(client, register):
    acc = register()
    r = client.post("/teams", json={"name": "x" * 31}, headers=acc["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_join_team(client, make_team, register):
    _, team = make_team()
    member = register("member@ex.com")
    r = client.post("/teams/join", json={"invite_code": team["invite_code"]}, headers=member["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == team["id"]
    # 합류 후 멤버 수 2
    me = client.get("/auth/me", headers=member["headers"]).json()
    assert me["team_id"] == team["id"]


def test_join_already_in_team_409(client, make_team, register):
    _, team_a = make_team("ownerA@ex.com", "팀A")
    _, team_b = make_team("ownerB@ex.com", "팀B")
    member = register("member@ex.com")
    client.post("/teams/join", json={"invite_code": team_a["invite_code"]}, headers=member["headers"])
    r = client.post("/teams/join", json={"invite_code": team_b["invite_code"]}, headers=member["headers"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_IN_TEAM"


def test_join_bad_code_format_400(client, register):
    acc = register()
    r = client.post("/teams/join", json={"invite_code": "abcd"}, headers=acc["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_join_nonexistent_code_404(client, register):
    acc = register()
    r = client.post("/teams/join", json={"invite_code": "ZZZZ-0000"}, headers=acc["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_get_team_as_member(client, make_team):
    acc, team = make_team()
    r = client.get(f"/teams/{team['id']}", headers=acc["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == team["id"]


def test_get_team_as_nonmember_403(client, make_team, register):
    _, team = make_team()
    outsider = register("outsider@ex.com")
    r = client.get(f"/teams/{team['id']}", headers=outsider["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_members_roles(client, make_team, join_member):
    owner, team = make_team()
    join_member(team["invite_code"], "m@ex.com")
    r = client.get(f"/teams/{team['id']}/members", headers=owner["headers"])
    assert r.status_code == 200
    roles = {m["email"]: m["role"] for m in r.json()}
    assert roles["owner@ex.com"] == "owner"
    assert roles["m@ex.com"] == "member"


def test_member_leave(client, make_team, join_member):
    _, team = make_team()
    member = join_member(team["invite_code"], "m@ex.com")
    r = client.delete(f"/teams/{team['id']}/leave", headers=member["headers"])
    assert r.status_code == 200
    me = client.get("/auth/me", headers=member["headers"]).json()
    assert me["team_id"] is None


def test_owner_cannot_leave_with_members_409(client, make_team, join_member):
    owner, team = make_team()
    join_member(team["invite_code"], "m@ex.com")
    r = client.delete(f"/teams/{team['id']}/leave", headers=owner["headers"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "OWNER_CANNOT_LEAVE"


def test_owner_leave_alone_deletes_team(client, make_team):
    owner, team = make_team()
    r = client.delete(f"/teams/{team['id']}/leave", headers=owner["headers"])
    assert r.status_code == 200
    # 팀 삭제 + owner의 team_id SET NULL
    me = client.get("/auth/me", headers=owner["headers"]).json()
    assert me["team_id"] is None
    # 삭제된 팀 재조회 시 비멤버 → 403
    r2 = client.get(f"/teams/{team['id']}", headers=owner["headers"])
    assert r2.status_code == 403
