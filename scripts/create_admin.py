#!/usr/bin/env python3
"""
Create admin user for Ethiopia Economic Data Platform

Credentials come from the ADMIN_EMAIL / ADMIN_PASSWORD environment variables.
If ADMIN_PASSWORD is not set you are prompted for it (or, when not running
interactively, a random password is generated and printed once).
"""

import os
import secrets
import sys
from datetime import datetime
from getpass import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import User, db
from werkzeug.security import generate_password_hash

DEFAULT_EMAIL = 'admin@ethiopia-economic.com'
MIN_PASSWORD_LENGTH = 12


def _get_password():
    password = os.environ.get('ADMIN_PASSWORD')
    if password:
        return password, False
    if sys.stdin.isatty():
        password = getpass('Admin password: ')
        if password != getpass('Confirm password: '):
            sys.exit('Passwords do not match.')
        return password, False
    return secrets.token_urlsafe(16), True


def create_admin_user():
    """Create the admin user if it does not exist yet"""
    app = create_app()
    email = os.environ.get('ADMIN_EMAIL', DEFAULT_EMAIL).strip().lower()

    with app.app_context():
        existing_admin = User.query.filter_by(email=email).first()

        if existing_admin:
            print(f"Admin user already exists: {email} (username: {existing_admin.username})")
            return

        password, generated = _get_password()
        if len(password) < MIN_PASSWORD_LENGTH:
            sys.exit(f'Admin password must be at least {MIN_PASSWORD_LENGTH} characters.')

        admin_user = User(
            username='admin',
            email=email,
            first_name='Admin',
            last_name='User',
            password_hash=generate_password_hash(password),
            role='admin',
            active=True,
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(admin_user)
            db.session.commit()

            print(f"Admin user created successfully: {email}")
            if generated:
                print("Generated password (shown once, store it securely):")
                print(password)

        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin_user()
