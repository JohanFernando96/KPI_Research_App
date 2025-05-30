# backend/utils/error_handlers.py

from flask import jsonify


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code or 400
        self.payload = payload

    def __str__(self):
        """Return string representation of the error."""
        return self.message

    def to_dict(self):
        rv = dict(self.payload or {})
        rv['message'] = self.message
        return rv


class KPIGenerationError(APIError):
    """KPI generation error."""

    def __init__(self, message="KPI generation failed", payload=None):
        super().__init__(message, 500, payload)


class TeamCompositionError(APIError):
    """Team composition error."""

    def __init__(self, message="Team composition error", payload=None):
        super().__init__(message, 400, payload)


class OptimizationError(APIError):
    """Optimization error."""

    def __init__(self, message="Optimization failed", payload=None):
        super().__init__(message, 500, payload)


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

    @app.errorhandler(KPIGenerationError)
    def handle_kpi_generation_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(TeamCompositionError)
    def handle_team_composition_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(OptimizationError)
    def handle_optimization_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404_error(error):
        response = jsonify({
            'success': False,
            'message': 'Resource not found'
        })
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def handle_500_error(error):
        # Log the actual error for debugging
        app.logger.error(f'Internal server error: {str(error)}')

        response = jsonify({
            'success': False,
            'message': 'Internal server error'
        })
        response.status_code = 500
        return response

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        # Log the actual error for debugging
        app.logger.error(f'Unhandled exception: {str(error)}')

        # Check if it's a werkzeug HTTP exception
        if hasattr(error, 'code'):
            response = jsonify({
                'success': False,
                'message': getattr(error, 'description', str(error))
            })
            response.status_code = getattr(error, 'code', 500)
            return response

        # Generic error response
        response = jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        })
        response.status_code = 500
        return response

    return app