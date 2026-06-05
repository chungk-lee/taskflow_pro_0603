"""Auth API (4): signup / login / logout / me."""


def test_signup_returns_token_and_user(client):
    r = client.post("/auth/signup", json={"email": "a@ex.com", "password": "password8"})
    assert r.status_code == 201
    data = r.json()
    assert data["token"]
    assert data["user"]["email"] == "a@ex.com"
    assert data["user"]["team_id"] is None  # 가입 직후 미소속
    assert "created_at" in data["user"]


def test_signup_duplicate_email_409(client, register):
    register("dup@ex.com")
    r = client.post("/auth/signup", json={"email": "dup@ex.com", "password": "password8"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


def test_signup_invalid_email_400(client):
    r = client.post("/auth/signup", json={"email": "not-an-email", "password": "password8"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_signup_short_password_400(client):
    r = client.post("/auth/signup", json={"email": "b@ex.com", "password": "short"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_success(client, register):
    register("login@ex.com", "password8")
    r = client.post("/auth/login", json={"email": "login@ex.com", "password": "password8"})
    assert r.status_code == 200
    assert r.json()["token"]


def test_login_wrong_password_401(client, register):
    register("c@ex.com", "password8")
    r = client.post("/auth/login", json={"email": "c@ex.com", "password": "wrongpass1"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_same_message_as_wrong_password(client, register):
    """이메일 존재 여부 비노출: 없는 이메일도 동일 코드/메시지."""
    register("known@ex.com", "password8")
    r_unknown = client.post("/auth/login", json={"email": "nobody@ex.com", "password": "password8"})
    r_wrong = client.post("/auth/login", json={"email": "known@ex.com", "password": "nopenope1"})
    assert r_unknown.status_code == r_wrong.status_code == 401
    assert r_unknown.json()["error"]["code"] == r_wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert r_unknown.json()["error"]["message"] == r_wrong.json()["error"]["message"]


def test_me_with_token(client, register):
    acc = register("me@ex.com")
    r = client.get("/auth/me", headers=acc["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == "me@ex.com"


def test_me_without_token_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_me_with_bad_token_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_logout_returns_ok(client, register):
    acc = register("out@ex.com")
    r = client.post("/auth/logout", headers=acc["headers"])
    assert r.status_code == 200
    assert r.json()["ok"] is True
