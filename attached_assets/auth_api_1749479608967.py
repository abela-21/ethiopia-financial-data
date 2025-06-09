from flask import Blueprint, request, jsonify, current_app
from api.models.models import User
from api.models import db, bcrypt
from api.utils.errors import APIError
from api.utils.limiter import limiter
from api.utils.cache import cache
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)
from datetime import datetime, timedelta
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)

auth_api = Blueprint("auth_api", __name__)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        raise APIError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise APIError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise APIError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise APIError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise APIError("Password must contain at least one special character")
    return True

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise APIError("Invalid email format")
    return True

@auth_api.route("/users/register", methods=["POST"])
@limiter.limit("5/minute")
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No input data provided", status_code=400)

        # Validate required fields
        required_fields = ["username", "password", "email"]
        for field in required_fields:
            if field not in data:
                raise APIError(f"Missing required field: {field}", status_code=400)

        # Validate username
        if len(data["username"]) < 3:
            raise APIError("Username must be at least 3 characters long", status_code=400)
        
        # Check existing username
        if User.query.filter_by(username=data["username"]).first():
            raise APIError("Username already exists", status_code=400)

        # Validate email
        validate_email(data["email"])
        if User.query.filter_by(email=data["email"]).first():
            raise APIError("Email already registered", status_code=400)

        # Validate password
        validate_password(data["password"])

        # Create new user
        hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_pw,
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )

        db.session.add(new_user)
        db.session.flush()
        user_id = new_user.id
        db.session.commit()

        logger.info(f"New user registered: {new_user.username}")

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id,
            "username": new_user.username
        }), 201

    except APIError as e:
        logger.warning(f"Registration failed: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@auth_api.route("/users/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No input data provided", status_code=400)

        # Validate required fields
        required_fields = ["username", "password"]
        for field in required_fields:
            if field not in data:
                raise APIError(f"Missing required field: {field}", status_code=400)

        user = User.query.filter_by(username=data["username"]).first()

        if not user:
            raise APIError("Invalid credentials", status_code=401)

        if not user.is_active:
            raise APIError("Account is disabled", status_code=403)

        if not bcrypt.check_password_hash(user.password, data["password"]):
            raise APIError("Invalid credentials", status_code=401)

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )

        logger.info(f"User logged in: {user.username}")

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }), 200

    except APIError as e:
        logger.warning(f"Login failed: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_api.route("/users/refresh", methods=["POST"])
@jwt_required(refresh=True)
@limiter.limit("10/minute")
def refresh_token():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.is_active:
            raise APIError("Invalid user or inactive account", status_code=401)

        new_access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )

        return jsonify({
            "access_token": new_access_token
        }), 200

    except APIError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_api.route("/users/profile", methods=["GET"])
@jwt_required()
@cache.cached(timeout=300)
def get_profile():
    """Get user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id) # Changed from .get_or_404()

        if not user:
            raise APIError("User not found", status_code=404) # Explicitly raise APIError for 404

        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        }), 200

    except APIError as e:
        logger.warning(f"Profile retrieval failed: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error getting profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500