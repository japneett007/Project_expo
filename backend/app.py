import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Security configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-change-in-production')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set True in production (HTTPS)
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # SameSite=Lax handles CSRF
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 24 hours
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    
    # CORS — allow frontend dev server
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
         supports_credentials=True)
    
    # JWT
    jwt = JWTManager(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.milestones import milestones_bp
    from routes.copilot import copilot_bp
    from routes.community import community_bp
    from routes.showcase import showcase_bp
    from routes.achievements import achievements_bp
    from routes.leaderboard import leaderboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(milestones_bp, url_prefix='/api/milestones')
    app.register_blueprint(copilot_bp, url_prefix='/api/copilot')
    app.register_blueprint(community_bp, url_prefix='/api/community')
    app.register_blueprint(showcase_bp, url_prefix='/api/showcase')
    app.register_blueprint(achievements_bp, url_prefix='/api/achievements')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'Project Hub V2 API is running'}

    # Security headers — applied to every response
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' http://localhost:5000"
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
