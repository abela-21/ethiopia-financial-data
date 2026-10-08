"""Authentication and authorization tests."""
import pytest

from conftest import ADMIN_EMAIL, ADMIN_PASSWORD, USER_EMAIL

ADMIN_PAGES = [
    "/admin", "/admin/manage-data", "/admin/data/companies", "/admin/data/financial",
    "/admin/data/banks", "/admin/data/research", "/admin/data/economic-indicators",
    "/admin/data/listed-companies", "/admin/data/users", "/admin/bulk-import",
    "/admin/external-data",
]


def test_login_page_renders(client):
    assert client.get("/auth/login").status_code == 200


def test_register_page_renders(client):
    assert client.get("/auth/register").status_code == 200


def test_login_wrong_password_stays_on_page(client):
    resp = client.post("/auth/login", data={"email": ADMIN_EMAIL, "password": "nope"})
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_login_missing_fields(client):
    resp = client.post("/auth/login", data={"email": "", "password": ""})
    assert resp.status_code == 200
    assert b"required" in resp.data


def test_login_is_case_insensitive_on_email(client):
    resp = client.post("/auth/login", data={"email": ADMIN_EMAIL.upper(), "password": ADMIN_PASSWORD})
    assert resp.status_code == 302


def test_register_then_login(client):
    form = {"first_name": "New", "last_name": "Person", "email": "new@test.local",
            "password": "abcdef1", "confirm_password": "abcdef1"}
    resp = client.post("/auth/register", data=form)
    assert resp.status_code == 302 and "/auth/login" in resp.headers["Location"]
    resp = client.post("/auth/login", data={"email": "new@test.local", "password": "abcdef1"})
    assert resp.status_code == 302


@pytest.mark.parametrize("override,message", [
    ({"confirm_password": "different"}, b"Passwords do not match"),
    ({"password": "abc", "confirm_password": "abc"}, b"at least 6"),
    ({"first_name": ""}, b"All fields are required"),
    ({"email": USER_EMAIL}, b"already registered"),
])
def test_register_validation(client, override, message):
    form = {"first_name": "A", "last_name": "B", "email": "v@test.local",
            "password": "abcdef1", "confirm_password": "abcdef1", **override}
    resp = client.post("/auth/register", data=form)
    assert resp.status_code == 200
    assert message in resp.data


def test_logout(admin_client):
    assert admin_client.get("/auth/logout").status_code == 302
    assert admin_client.get("/admin").status_code == 302


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_redirect_anonymous(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_reject_regular_user(user_client, path):
    resp = user_client.get(path)
    assert resp.status_code in (302, 403)


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_render_for_admin(admin_client, path):
    assert admin_client.get(path).status_code == 200


def test_admin_json_api_rejects_regular_user(user_client):
    resp = user_client.get("/admin/api/indicator/1")
    assert resp.status_code in (302, 403)


@pytest.mark.xfail(reason="Open redirect: login follows any ?next= URL, including external sites", strict=True)
def test_login_next_param_does_not_redirect_offsite(client):
    resp = client.post("/auth/login?next=https://evil.example.com/",
                       data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert "evil.example.com" not in resp.headers.get("Location", "")
