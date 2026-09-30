import os

import pytest


@pytest.fixture
def app(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"

    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite:///{test_db}",
    )

    monkeypatch.setenv(
        "SEED_DATABASE",
        "false",
    )

    from app import create_app, db

    app = create_app()

    app.config.update(
        TESTING=True,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()