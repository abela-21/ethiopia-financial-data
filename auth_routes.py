from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not all([first_name, last_name, email, password]):
                flash('All fields are required', 'error')
                return render_template('auth/register.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('auth/register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('auth/register.html')
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email address already registered', 'error')
                return render_template('auth/register.html')
            
            # Create username from email (before @)
            username = email.split('@')[0]
            
            # Check if username exists, if so add numbers
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=generate_password_hash(password),
                role='user',
                active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('auth/login.html')
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.active:
                    flash('Account is deactivated. Please contact support.', 'error')
                    return render_template('auth/login.html')
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log user in
                login_user(user)
                
                # Set session data
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                session['role'] = user.role
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                
                flash(f'Welcome back, {user.first_name}!', 'success')
                
                # Redirect to requested page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Update user information
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            
            # Handle password change if provided
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            
            if new_password:
                if not current_password:
                    flash('Current password required to change password', 'error')
                    return render_template('auth/edit_profile.html', user=current_user)
                
                if not current_user.check_password(current_password):
                    flash('Current password is incorrect', 'error')
                    return render_template('auth/edit_profile.html', user=current_user)
                
                if len(new_password) < 6:
                    flash('New password must be at least 6 characters long', 'error')
                    return render_template('auth/edit_profile.html', user=current_user)
                
                current_user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            
            # Update session data
            session['first_name'] = current_user.first_name
            session['last_name'] = current_user.last_name
            
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            db.session.rollback()
            flash('Profile update failed. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)