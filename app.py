"""
Buyi Trust Protocol — Flask Application
Serves cert.diubige.com

Endpoints:
  GET  /<cert_id>              → Certificate share page (HTML)
  POST /api/certificate        → Create certificate
  POST /api/certificate/<id>/verify → Submit verification
  GET  /api/certificate/<id>   → Get certificate + verifications (JSON)
  GET  /api/reputation/<pid>   → Get provider reputation (JSON)
"""

import os
import sys

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from cert_api import cert_bp
from pages import page_bp
from db import init_db, close_db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    
    # Register blueprints
    app.register_blueprint(cert_bp)   # /api/certificate/*
    app.register_blueprint(page_bp)   # /<cert_id>
    
    # Teardown
    app.teardown_appcontext(close_db)
    
    # Health check
    @app.route('/health')
    def health():
        return {"status": "ok", "service": "Buyi Trust Protocol"}
    
    return app
