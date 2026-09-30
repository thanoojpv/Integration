from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from . import db
from .models import User


def make_token(user):
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }

    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )


def verify_token():
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        return None, (
            jsonify({
                "error": "Authorization token is required"
            }),
            401,
        )

    token = header.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )

        user = db.session.get(User, payload["sub"])

        if not user:
            raise ValueError("User not found")

        # Reject tokens belonging to inactive/suspended accounts.
        if user.status != "active":
            return None, (
                jsonify({
                    "error": "Your account is inactive"
                }),
                403,
            )

        return user, None

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
    ):
        return None, (
            jsonify({
                "error": "Invalid or expired token"
            }),
            401,
        )


def login_user(email, password):
    user = User.query.filter_by(
        email=email.lower().strip()
    ).first()

    # Do not reveal whether the account exists.
    if not user:
        return None

    now = datetime.now(timezone.utc)

    # SQLite/MySQL may return a naive datetime even when the
    # model uses timezone-aware DateTime.
    if user.locked_until:
        locked_until = user.locked_until

        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)

        if locked_until > now:
            return None

        # Lockout period has expired.
        user.locked_until = None
        user.failed_login_attempts = 0
        db.session.commit()

    # Check password.
    if not check_password_hash(
        user.password_hash,
        password
    ):
        user.failed_login_attempts += 1

        # Lock after 5 consecutive failed attempts.
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)

        db.session.commit()
        return None

    # Successful login resets the failed-attempt counter.
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    return user


def create_password_hash(password):
    return generate_password_hash(password)


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user, error = verify_token()

        if error:
            return error

        return fn(user, *args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @token_required
        def wrapper(user, *args, **kwargs):
            if user.role not in roles:
                return jsonify({
                    "error": "You do not have permission for this action"
                }), 403

            return fn(user, *args, **kwargs)

        return wrapper

    return decorator