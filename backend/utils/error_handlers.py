from flask import jsonify


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(self)
        self.message = message
        self.status_code = status_code or 400
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or {})
        rv['message'] = self.message
        return rv


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, 404, payload)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message="Validation error", payload=None):
        super().__init__(message, 400, payload)


class AuthorizationError(APIError):
    """Authorization error."""

    def __init__(self, message="Authorization error", payload=None):
        super().__init__(message, 403, payload)


def register_error_handlers(app):
    """Register error handlers for the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404_error(error):
        response = jsonify({
            'message': 'Resource not found'
        })
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def handle_500_error(error):
        response = jsonify({
            'message': 'Internal server error'
        })
        response.status_code = 500
        return response

    return app