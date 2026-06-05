"""Task API (6): list/create + get/update/status/delete + 권한·필터·assignee 규칙."""


def _create_task(client, headers, team_id, title="할 일", **extra):
    r = client.post(f"/teams/{team_id}/tasks", json={"title": title, **extra}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_task_defaults(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"], "첫 카드")
    assert task["title"] == "첫 카드"
    assert task["status"] == "TODO"  # 기본 상태
    assert task["assignee_id"] is None  # 기본 미할당
    assert task["creator_id"] == acc["user"]["id"]


def test_create_task_assign_self(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"], assignee_id=acc["user"]["id"])
    assert task["assignee_id"] == acc["user"]["id"]


def test_create_task_assignee_not_in_team_400(client, make_team, register):
    acc, team = make_team()
    outsider = register("out@ex.com")
    r = client.post(
        f"/teams/{team['id']}/tasks",
        json={"title": "x", "assignee_id": outsider["user"]["id"]},
        headers=acc["headers"],
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_task_title_too_long_400(client, make_team):
    acc, team = make_team()
    r = client.post(f"/teams/{team['id']}/tasks", json={"title": "x" * 101}, headers=acc["headers"])
    assert r.status_code == 400


def test_create_task_nonmember_403(client, make_team, register):
    _, team = make_team()
    outsider = register("out@ex.com")
    r = client.post(f"/teams/{team['id']}/tasks", json={"title": "x"}, headers=outsider["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_list_filters(client, make_team, join_member):
    owner, team = make_team()
    member = join_member(team["invite_code"], "m@ex.com")
    # owner 담당 1, 미할당 1, member 담당 1
    _create_task(client, owner["headers"], team["id"], "owner것", assignee_id=owner["user"]["id"])
    _create_task(client, owner["headers"], team["id"], "미할당것")
    _create_task(client, owner["headers"], team["id"], "member것", assignee_id=member["user"]["id"])

    all_ = client.get(f"/teams/{team['id']}/tasks", headers=owner["headers"]).json()
    assert len(all_) == 3

    mine = client.get(f"/teams/{team['id']}/tasks?filter=me", headers=owner["headers"]).json()
    assert [t["title"] for t in mine] == ["owner것"]

    unassigned = client.get(f"/teams/{team['id']}/tasks?filter=unassigned", headers=owner["headers"]).json()
    assert [t["title"] for t in unassigned] == ["미할당것"]


def test_list_order_recent_first(client, make_team):
    acc, team = make_team()
    _create_task(client, acc["headers"], team["id"], "오래된")
    _create_task(client, acc["headers"], team["id"], "최신")
    tasks = client.get(f"/teams/{team['id']}/tasks", headers=acc["headers"]).json()
    # created_at desc, id desc → 최신이 먼저
    assert tasks[0]["title"] == "최신"


def test_get_single_task(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"])
    r = client.get(f"/tasks/{task['id']}", headers=acc["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == task["id"]


def test_get_task_other_team_403(client, make_team):
    owner_a, team_a = make_team("a@ex.com", "팀A")
    task = _create_task(client, owner_a["headers"], team_a["id"])
    owner_b, _ = make_team("b@ex.com", "팀B")
    r = client.get(f"/tasks/{task['id']}", headers=owner_b["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_get_task_not_found_404(client, make_team):
    acc, _ = make_team()
    r = client.get("/tasks/99999", headers=acc["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_update_task_title_and_assignee(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"], "원제목")
    r = client.put(
        f"/tasks/{task['id']}",
        json={"title": "새제목", "assignee_id": acc["user"]["id"]},
        headers=acc["headers"],
    )
    assert r.status_code == 200
    assert r.json()["title"] == "새제목"
    assert r.json()["assignee_id"] == acc["user"]["id"]


def test_patch_status(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"])
    r = client.patch(f"/tasks/{task['id']}/status", json={"status": "DONE"}, headers=acc["headers"])
    assert r.status_code == 200
    assert r.json()["status"] == "DONE"


def test_patch_status_invalid_400(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"])
    r = client.patch(f"/tasks/{task['id']}/status", json={"status": "NOPE"}, headers=acc["headers"])
    assert r.status_code == 400


def test_delete_task_by_creator(client, make_team):
    acc, team = make_team()
    task = _create_task(client, acc["headers"], team["id"])
    r = client.delete(f"/tasks/{task['id']}", headers=acc["headers"])
    assert r.status_code == 200
    assert client.get(f"/tasks/{task['id']}", headers=acc["headers"]).status_code == 404


def test_delete_task_owner_override(client, make_team, join_member):
    """owner는 타인(멤버) 카드도 삭제 가능."""
    owner, team = make_team()
    member = join_member(team["invite_code"], "m@ex.com")
    task = _create_task(client, member["headers"], team["id"], "멤버카드")
    r = client.delete(f"/tasks/{task['id']}", headers=owner["headers"])
    assert r.status_code == 200


def test_delete_task_member_cannot_delete_others_403(client, make_team, join_member):
    """멤버는 본인 카드만 삭제. owner 카드 삭제 시도 → 403."""
    owner, team = make_team()
    member = join_member(team["invite_code"], "m@ex.com")
    task = _create_task(client, owner["headers"], team["id"], "owner카드")
    r = client.delete(f"/tasks/{task['id']}", headers=member["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"
