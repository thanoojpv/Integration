from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate


load_dotenv()


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=os.getenv(
        "LOG_LEVEL",
        "INFO"
    ).upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

db = SQLAlchemy()
migrate = Migrate()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    ),
)


# =========================================================
# APPLICATION
# =========================================================

def create_app():

    app = Flask(
        __name__,
        instance_relative_config=True
    )

    os.makedirs(
        app.instance_path,
        exist_ok=True
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "devsprint-development-secret-change-me"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(app.root_path),
        "uploads"
    )

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    # =====================================================
    # CORS
    # =====================================================

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": os.getenv(
                    "FRONTEND_ORIGIN",
                    "http://localhost:5173"
                )
            }
        }
    )

    # =====================================================
    # DATABASE + MIGRATIONS
    # =====================================================

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )
    limiter.init_app(app)

    # =====================================================
    # ROUTES
    # =====================================================

    from .routes import api

    app.register_blueprint(
        api,
        url_prefix="/api"
    )

    # =====================================================
    # OPTIONAL DATABASE SEEDING
    # =====================================================

    with app.app_context():

        if os.getenv(
            "SEED_DATABASE",
            "false"
        ).lower() == "true":

            from .seed import seed_database

            seed_database()

    # =====================================================
    # STARTUP LOG
    # =====================================================

    logger.info(
        "DevSprint LMS application initialized"
    )

    return app