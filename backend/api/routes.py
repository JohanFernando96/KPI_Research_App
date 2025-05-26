def register_blueprints(app):
    """Register Flask blueprints."""
    from api.endpoints.cv_routes import cv_blueprint
    from api.endpoints.employee_routes import employee_blueprint
    from api.endpoints.project_routes import project_blueprint
    from api.endpoints.kpi_routes import kpi_blueprint
    from api.endpoints.recommendation_routes import recommendation_blueprint
    from api.endpoints.skill_development_routes import skill_development_blueprint  # New

    app.register_blueprint(cv_blueprint, url_prefix='/api/cv')
    app.register_blueprint(employee_blueprint, url_prefix='/api/employees')
    app.register_blueprint(project_blueprint, url_prefix='/api/projects')
    app.register_blueprint(kpi_blueprint, url_prefix='/api/kpi')
    app.register_blueprint(recommendation_blueprint, url_prefix='/api/recommendations')
    app.register_blueprint(skill_development_blueprint, url_prefix='/api/skill-development')  # New

    # Register error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app