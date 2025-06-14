#!/usr/bin/env python3
"""
Test script to verify admin panel functionality
"""

from app import create_app
from models import User, db
from flask_login import login_user
import logging

def test_admin_panel():
    """Test admin panel data and display"""
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(email='admin@ethiopia-economic.com').first()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return
        
        print(f"✅ Admin user found: {admin_user.first_name} {admin_user.last_name}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print(f"   Active: {admin_user.active}")
        print()
        
        # Get admin panel statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        print("📊 ADMIN PANEL STATISTICS:")
        print(f"   Total Users: {total_users}")
        print(f"   Active Users: {active_users}")
        print(f"   Admin Users: {admin_users}")
        print(f"   Recent Users: {len(recent_users)}")
        print()
        
        print("👥 RECENT USERS:")
        for i, user in enumerate(recent_users, 1):
            print(f"   {i}. {user.first_name} {user.last_name} ({user.email})")
            print(f"      Role: {user.role} | Active: {user.active}")
            print(f"      Joined: {user.created_at.strftime('%B %d, %Y')}")
            print()
        
        # Test admin route access
        with app.test_client() as client:
            # Test admin panel route directly
            try:
                # Simulate login
                with client.session_transaction() as sess:
                    sess['user_id'] = admin_user.id
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                
                response = client.get('/admin')
                print(f"🌐 Admin Panel Route Test:")
                print(f"   Status Code: {response.status_code}")
                print(f"   Contains 'Admin Panel': {'Admin Panel' in response.get_data(as_text=True)}")
                print(f"   Contains statistics: {'Total Users' in response.get_data(as_text=True)}")
                
            except Exception as e:
                print(f"❌ Error testing admin route: {e}")

if __name__ == '__main__':
    test_admin_panel()