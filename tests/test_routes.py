"""Route-level tests: auth walls and public pages (no database needed)."""


def test_home_page_is_public(client):
    assert client.get("/").status_code == 200


def test_login_and_register_pages_are_public(client):
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200


def test_protected_pages_redirect_when_logged_out(client):
    for path in ["/dashboard", "/history", "/recurring", "/balance", "/report"]:
        resp = client.get(path)
        assert resp.status_code == 302, path
        assert "auth=required" in resp.headers["Location"], path


def test_submit_requires_login(client):
    resp = client.post("/submit", data={"amount": "100"})
    assert resp.status_code == 302
    assert "auth=required" in resp.headers["Location"]


def test_delete_requires_login(client):
    resp = client.post("/delete/1")
    assert resp.status_code == 302


def test_budget_set_requires_login(client):
    resp = client.post("/budget/set", data={"amount": "5000"})
    assert resp.status_code == 302


def test_api_endpoints_reject_logged_out_users(client):
    for path in ["/api/chart-data", "/api/due-recurring"]:
        resp = client.get(path)
        assert resp.status_code == 401, path
        assert resp.get_json()["error"] == "auth required"


def test_setup_db_rejected_outside_cloud(client):
    # Locally (no DATABASE_URL) this route must refuse to run
    resp = client.get("/setup-db?key=whatever")
    assert resp.status_code == 400
