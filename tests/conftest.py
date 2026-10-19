import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """Flask app bound to a throwaway SQLite file.

    app.py runs init_db()/seed_db() at import time, so DB_PATH must be
    redirected before `app` is imported.
    """
    import database.db as db_module

    db_file = tmp_path_factory.mktemp("spendly_db") / "test_spendly.db"
    mp = pytest.MonkeyPatch()
    mp.setattr(db_module, "DB_PATH", str(db_file))

    import app as app_module  # noqa: E402  (import must follow the patch)

    flask_app = app_module.app
    flask_app.config.update(TESTING=True, SECRET_KEY="test-secret")
    yield flask_app
    mp.undo()


@pytest.fixture
def client(app):
    """Anonymous test client (fresh cookie jar per test)."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Test client logged in as the seeded demo user via POST /login."""
    response = client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, "Demo login should redirect on success"
    return client
