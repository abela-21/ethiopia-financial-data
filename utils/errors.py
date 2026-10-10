from flask import jsonify, request, render_template, flash, redirect
from flask_wtf.csrf import CSRFError
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API exception class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        result = dict(self.payload or ())
        result['error'] = self.message
        return result

def _wants_json():
    """API and fetch() callers get JSON; browsers navigating pages get HTML."""
    if request.path.startswith('/api/') or '/api/' in request.path or request.is_json:
        return True
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def _error_response(message, status_code):
    if _wants_json():
        return jsonify({'error': message}), status_code
    return render_template('error.html', status_code=status_code, message=message), status_code

def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.warning(f"API Error: {error.message} (Status: {error.status_code})")
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        logger.warning(f"CSRF validation failed on {request.path}: {error.description}")
        if _wants_json() or request.method != 'POST' or not request.form:
            return jsonify({'error': 'CSRF token missing or invalid. Reload the page and try again.'}), 400
        flash('Your session expired. Please try again.', 'error')
        return redirect(request.url)

    @app.errorhandler(404)
    def handle_not_found(error):
        return _error_response('Resource not found', 404)

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return _error_response('Internal server error', 500)

    @app.errorhandler(400)
    def handle_bad_request(error):
        return _error_response('Bad request', 400)

    @app.errorhandler(401)
    def handle_unauthorized(error):
        return _error_response('Unauthorized access', 401)

    @app.errorhandler(403)
    def handle_forbidden(error):
        return _error_response('Forbidden access', 403)

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return _error_response('Rate limit exceeded', 429)
