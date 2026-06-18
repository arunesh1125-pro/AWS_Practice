from flask import Flask, jsonify
import os

# Elastic Beanstalk expects the WSGI callable named 'application' by default
application = Flask(__name__)

@application.route('/')
def home():
    return jsonify({
        "status": "Online",
        "service": "Elastic Beanstalk Environment Workspace",
        "injected_bucket": os.environ.get('MODEL_BUCKET', 'Not_Set'),
        "env_context": os.environ.get('ENVIRONMENT', 'development')
    })

if __name__ == '__main__':
    # Run locally on port 5000 for standard verification tracking
    application.run(host='0.0.0.0', port=5000)
