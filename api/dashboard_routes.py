from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import (UserWatchlist, WatchlistCompany, DownloadHistory, 
                   UserAlert, UserPreference, SavedSearch, Company)
from datetime import datetime, timedelta
import json
import logging

dashboard_bp = Blueprint('dashboard_api', __name__)

@dashboard_bp.route('/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    try:
        # Count watchlists
        watchlist_count = UserWatchlist.query.filter_by(user_id=current_user.id).count()
        
        # Count companies in all watchlists
        companies_count = db.session.query(WatchlistCompany)\
            .join(UserWatchlist)\
            .filter(UserWatchlist.user_id == current_user.id)\
            .count()
        
        # Count downloads in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        downloads_count = DownloadHistory.query\
            .filter_by(user_id=current_user.id)\
            .filter(DownloadHistory.downloaded_at >= thirty_days_ago)\
            .count()
        
        # Count active alerts
        alerts_count = UserAlert.query\
            .filter_by(user_id=current_user.id, is_active=True)\
            .count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'watchlist_count': watchlist_count,
                'companies_count': companies_count,
                'downloads_count': downloads_count,
                'alerts_count': alerts_count
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load dashboard statistics'}), 500

@dashboard_bp.route('/dashboard/watchlists', methods=['GET'])
@login_required
def get_watchlists():
    """Get all watchlists for the current user"""
    try:
        watchlists = UserWatchlist.query.filter_by(user_id=current_user.id)\
            .order_by(UserWatchlist.is_default.desc(), UserWatchlist.created_at.desc())\
            .all()
        
        watchlist_data = []
        for watchlist in watchlists:
            companies_count = len(watchlist.companies)
            watchlist_data.append({
                'id': watchlist.id,
                'name': watchlist.name,
                'description': watchlist.description,
                'is_default': watchlist.is_default,
                'is_public': watchlist.is_public,
                'companies_count': companies_count,
                'created_at': watchlist.created_at.isoformat(),
                'updated_at': watchlist.updated_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': watchlist_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting watchlists: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load watchlists'}), 500

@dashboard_bp.route('/dashboard/watchlists', methods=['POST'])
@login_required
def create_watchlist():
    """Create a new watchlist"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'status': 'error', 'message': 'Watchlist name is required'}), 400
        
        # If this is set as default, unset others
        if data.get('is_default'):
            UserWatchlist.query.filter_by(user_id=current_user.id, is_default=True)\
                .update({'is_default': False})
        
        # Create new watchlist
        watchlist = UserWatchlist(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description', ''),
            is_default=data.get('is_default', False),
            is_public=data.get('is_public', False)
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Watchlist created successfully',
            'data': {
                'id': watchlist.id,
                'name': watchlist.name,
                'description': watchlist.description,
                'is_default': watchlist.is_default,
                'is_public': watchlist.is_public,
                'companies_count': 0,
                'created_at': watchlist.created_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating watchlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create watchlist'}), 500

@dashboard_bp.route('/dashboard/watchlists/<int:watchlist_id>', methods=['PUT'])
@login_required
def update_watchlist(watchlist_id):
    """Update a watchlist"""
    try:
        watchlist = UserWatchlist.query.filter_by(
            id=watchlist_id, user_id=current_user.id
        ).first()
        
        if not watchlist:
            return jsonify({'status': 'error', 'message': 'Watchlist not found'}), 404
        
        data = request.get_json()
        
        # If this is set as default, unset others
        if data.get('is_default') and not watchlist.is_default:
            UserWatchlist.query.filter_by(user_id=current_user.id, is_default=True)\
                .update({'is_default': False})
        
        # Update watchlist
        if 'name' in data:
            watchlist.name = data['name']
        if 'description' in data:
            watchlist.description = data['description']
        if 'is_default' in data:
            watchlist.is_default = data['is_default']
        if 'is_public' in data:
            watchlist.is_public = data['is_public']
        
        watchlist.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Watchlist updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating watchlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to update watchlist'}), 500

@dashboard_bp.route('/dashboard/watchlists/<int:watchlist_id>', methods=['DELETE'])
@login_required
def delete_watchlist(watchlist_id):
    """Delete a watchlist"""
    try:
        watchlist = UserWatchlist.query.filter_by(
            id=watchlist_id, user_id=current_user.id
        ).first()
        
        if not watchlist:
            return jsonify({'status': 'error', 'message': 'Watchlist not found'}), 404
        
        db.session.delete(watchlist)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Watchlist deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting watchlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to delete watchlist'}), 500

@dashboard_bp.route('/dashboard/watchlists/<int:watchlist_id>/companies')
@login_required
def get_watchlist_companies(watchlist_id):
    """Get companies in a specific watchlist"""
    try:
        watchlist = UserWatchlist.query.filter_by(
            id=watchlist_id, user_id=current_user.id
        ).first()
        
        if not watchlist:
            return jsonify({'status': 'error', 'message': 'Watchlist not found'}), 404
        
        companies = db.session.query(WatchlistCompany, Company)\
            .join(Company, WatchlistCompany.company_id == Company.id)\
            .filter(WatchlistCompany.watchlist_id == watchlist_id)\
            .order_by(WatchlistCompany.added_at.desc())\
            .all()
        
        company_data = []
        for wc, company in companies:
            company_data.append({
                'id': company.id,
                'name': company.name,
                'ticker': company.ticker,
                'sector': company.sector,
                'added_at': wc.added_at.isoformat(),
                'notes': wc.notes,
                'price_alert_enabled': wc.price_alert_enabled,
                'target_price': float(wc.target_price) if wc.target_price else None,
                'alert_type': wc.alert_type
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'watchlist': {
                    'id': watchlist.id,
                    'name': watchlist.name,
                    'description': watchlist.description
                },
                'companies': company_data
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting watchlist companies: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load watchlist companies'}), 500

@dashboard_bp.route('/dashboard/watchlists/<int:watchlist_id>/companies', methods=['POST'])
@login_required
def add_company_to_watchlist(watchlist_id):
    """Add a company to a watchlist"""
    try:
        watchlist = UserWatchlist.query.filter_by(
            id=watchlist_id, user_id=current_user.id
        ).first()
        
        if not watchlist:
            return jsonify({'status': 'error', 'message': 'Watchlist not found'}), 404
        
        data = request.get_json()
        company_id = data.get('company_id')
        
        if not company_id:
            return jsonify({'status': 'error', 'message': 'Company ID is required'}), 400
        
        # Check if company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'status': 'error', 'message': 'Company not found'}), 404
        
        # Check if already in watchlist
        existing = WatchlistCompany.query.filter_by(
            watchlist_id=watchlist_id, company_id=company_id
        ).first()
        
        if existing:
            return jsonify({'status': 'error', 'message': 'Company already in watchlist'}), 400
        
        # Add to watchlist
        watchlist_company = WatchlistCompany(
            watchlist_id=watchlist_id,
            company_id=company_id,
            notes=data.get('notes', ''),
            price_alert_enabled=data.get('price_alert_enabled', False),
            target_price=data.get('target_price'),
            alert_type=data.get('alert_type')
        )
        
        db.session.add(watchlist_company)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'{company.name} added to watchlist successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding company to watchlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to add company to watchlist'}), 500

@dashboard_bp.route('/dashboard/download-history')
@login_required
def get_download_history():
    """Get download history for the current user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        downloads = DownloadHistory.query\
            .filter_by(user_id=current_user.id)\
            .order_by(DownloadHistory.downloaded_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        download_data = []
        for download in downloads.items:
            download_data.append({
                'id': download.id,
                'download_type': download.download_type,
                'resource_name': download.resource_name,
                'file_format': download.file_format,
                'file_size': download.file_size,
                'status': download.status,
                'downloaded_at': download.downloaded_at.isoformat(),
                'expires_at': download.expires_at.isoformat() if download.expires_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'downloads': download_data,
                'pagination': {
                    'page': downloads.page,
                    'pages': downloads.pages,
                    'per_page': downloads.per_page,
                    'total': downloads.total,
                    'has_next': downloads.has_next,
                    'has_prev': downloads.has_prev
                }
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting download history: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load download history'}), 500

@dashboard_bp.route('/dashboard/saved-searches')
@login_required
def get_saved_searches():
    """Get saved searches for the current user"""
    try:
        searches = SavedSearch.query\
            .filter_by(user_id=current_user.id)\
            .order_by(SavedSearch.updated_at.desc())\
            .all()
        
        search_data = []
        for search in searches:
            search_data.append({
                'id': search.id,
                'name': search.name,
                'description': search.description,
                'alert_enabled': search.alert_enabled,
                'alert_frequency': search.alert_frequency,
                'results_count': search.results_count,
                'last_executed': search.last_executed.isoformat() if search.last_executed else None,
                'created_at': search.created_at.isoformat(),
                'updated_at': search.updated_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': search_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting saved searches: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load saved searches'}), 500

@dashboard_bp.route('/dashboard/recent-activity')
@login_required
def get_recent_activity():
    """Get recent activity for the current user"""
    try:
        # Get recent downloads
        recent_downloads = DownloadHistory.query\
            .filter_by(user_id=current_user.id)\
            .order_by(DownloadHistory.downloaded_at.desc())\
            .limit(5)\
            .all()
        
        # Get recent watchlist additions
        recent_watchlist_additions = db.session.query(WatchlistCompany, Company, UserWatchlist)\
            .join(Company, WatchlistCompany.company_id == Company.id)\
            .join(UserWatchlist, WatchlistCompany.watchlist_id == UserWatchlist.id)\
            .filter(UserWatchlist.user_id == current_user.id)\
            .order_by(WatchlistCompany.added_at.desc())\
            .limit(5)\
            .all()
        
        activities = []
        
        # Add download activities
        for download in recent_downloads:
            activities.append({
                'type': 'download',
                'description': f'Downloaded {download.resource_name}',
                'timestamp': download.downloaded_at.isoformat(),
                'details': {
                    'file_format': download.file_format,
                    'download_type': download.download_type
                }
            })
        
        # Add watchlist activities
        for wc, company, watchlist in recent_watchlist_additions:
            activities.append({
                'type': 'watchlist_addition',
                'description': f'Added {company.name} to {watchlist.name}',
                'timestamp': wc.added_at.isoformat(),
                'details': {
                    'company_ticker': company.ticker,
                    'watchlist_name': watchlist.name
                }
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': activities[:10]  # Return top 10 activities
        })
    except Exception as e:
        current_app.logger.error(f"Error getting recent activity: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load recent activity'}), 500

@dashboard_bp.route('/dashboard/alerts')
@login_required
def get_user_alerts():
    """Get alerts for the current user"""
    try:
        alert_type = request.args.get('type', 'all')
        
        query = UserAlert.query.filter_by(user_id=current_user.id)
        
        if alert_type != 'all':
            query = query.filter_by(alert_type=alert_type)
        
        alerts = query.order_by(UserAlert.created_at.desc()).all()
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'company_id': alert.company_id,
                'is_active': alert.is_active,
                'frequency': alert.frequency,
                'delivery_method': alert.delivery_method,
                'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                'created_at': alert.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': alert_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user alerts: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load alerts'}), 500

@dashboard_bp.route('/dashboard/preferences')
@login_required
def get_user_preferences():
    """Get user preferences"""
    try:
        preferences = UserPreference.query.filter_by(user_id=current_user.id).all()
        
        pref_data = {}
        for pref in preferences:
            if pref.category not in pref_data:
                pref_data[pref.category] = {}
            
            try:
                # Try to parse as JSON, fallback to string
                value = json.loads(pref.preference_value)
            except (json.JSONDecodeError, TypeError):
                value = pref.preference_value
            
            pref_data[pref.category][pref.preference_key] = value
        
        return jsonify({
            'status': 'success',
            'data': pref_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user preferences: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load preferences'}), 500

@dashboard_bp.route('/dashboard/preferences', methods=['POST'])
@login_required
def update_user_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        
        for category, preferences in data.items():
            for key, value in preferences.items():
                # Convert value to JSON string if it's not a string
                if not isinstance(value, str):
                    value = json.dumps(value)
                
                # Update or create preference
                pref = UserPreference.query.filter_by(
                    user_id=current_user.id,
                    preference_key=key,
                    category=category
                ).first()
                
                if pref:
                    pref.preference_value = value
                    pref.updated_at = datetime.utcnow()
                else:
                    pref = UserPreference(
                        user_id=current_user.id,
                        preference_key=key,
                        preference_value=value,
                        category=category
                    )
                    db.session.add(pref)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Preferences updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user preferences: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to update preferences'}), 500