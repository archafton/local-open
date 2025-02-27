from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
from utils.exceptions import AppError, ResourceNotFoundError, ValidationError, DatabaseError

def create_app():
    # Set up logging with absolute path
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, 'api.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Log startup message
    logging.info("API server starting up")
    
    app = Flask(__name__)
    
    # Configure the app
    app.config['DB_CONNECTION_STRING'] = os.environ.get('DATABASE_URL') or "postgresql://localhost/project_tacitus_test"
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    
    # Enable CORS with specific configuration
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}}, supports_credentials=True)
    
    # Register error handlers
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logging.error(f"AppError: {str(error)}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    # Add more error handlers as in the artifact
    
    # Register blueprints
    from api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
