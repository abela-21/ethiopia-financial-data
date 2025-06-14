#!/usr/bin/env python3
"""
Create admin user for Ethiopia Economic Data Platform
"""

from app import create_app
from models import User, db
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    """Create default admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@ethiopia-economic.com').first()
        
        if existing_admin:
            print("Admin user already exists!")
            print(f"Email: admin@ethiopia-economic.com")
            print(f"Username: {existing_admin.username}")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@ethiopia-economic.com',
            first_name='Admin',
            last_name='User',
            password_hash=generate_password_hash('EthiopiaAdmin2024!'),
            role='admin',
            active=True,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            
            print("Admin user created successfully!")
            print("=" * 50)
            print("ADMIN LOGIN CREDENTIALS:")
            print("Email: admin@ethiopia-economic.com")
            print("Password: EthiopiaAdmin2024!")
            print("=" * 50)
            print("Please save these credentials securely!")
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin_user()