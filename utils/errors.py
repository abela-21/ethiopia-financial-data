from flask import jsonify
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

def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.warning(f"API Error: {error.message} (Status: {error.status_code})")
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        return jsonify({'error': 'Unauthorized access'}), 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        return jsonify({'error': 'Forbidden access'}), 403

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify({'error': 'Rate limit exceeded'}), 429
