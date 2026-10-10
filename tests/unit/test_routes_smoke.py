"""
Smoke test every parameter-free GET route: nothing should return a 5xx,
for anonymous visitors or for a logged-in admin.
"""
import pytest

from app import app as flask_app

# Routes that intentionally call external services or long-running jobs.
SKIP = {"/admin/data/refresh", "/admin/api/refresh-data"}


def _get_routes():
    out = []
    for rule in flask_app.url_map.iter_rules():
        if "GET" not in rule.methods or rule.arguments or rule.endpoint == "static":
            continue
        if rule.rule in SKIP:
            continue
        out.append(rule.rule)
    return sorted(set(out))


# Known application bugs, kept visible as strict xfails.
KNOWN_BROKEN = {}


def _params(routes):
    return [
        pytest.param(r, marks=pytest.mark.xfail(reason=KNOWN_BROKEN[r], strict=True))
        if r in KNOWN_BROKEN else r
        for r in routes
    ]


GET_ROUTES = _get_routes()


def test_route_discovery_found_routes():
    assert len(GET_ROUTES) > 40


@pytest.mark.parametrize("path", GET_ROUTES)
def test_anonymous_get_has_no_server_error(client, path):
    resp = client.get(path)
    assert resp.status_code < 500, f"{path} -> {resp.status_code}: {resp.data[:300]!r}"


@pytest.mark.parametrize("path", _params(GET_ROUTES))
def test_admin_get_has_no_server_error(admin_client, path):
    resp = admin_client.get(path)
    assert resp.status_code < 500, f"{path} -> {resp.status_code}: {resp.data[:300]!r}"


def test_unknown_route_is_404(client):
    assert client.get("/definitely-not-a-page").status_code == 404
