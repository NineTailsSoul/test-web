# config.py

import os
from dotenv import load_dotenv

# Load environment variables from a .env file.
# This ensures that variables like SECRET_KEY can be set in a .env file
# locally or as Codespaces Secrets.
load_dotenv()

class Config:
    # --- Essential Flask Configuration ---
    # SECRET_KEY is crucial for session security and other Flask features.
    # Get it from an environment variable, or use a strong default for development.
    # For production, set this via environment variables (e.g., Codespaces Secrets).
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_super_secret_key_here_please_change_this_default')

    # --- Flask-Session Configuration ---
    # Using 'filesystem' as the session type means sessions will be stored in files
    # on the server's filesystem, rather than in a database like MongoDB.
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False # Sessions will not expire automatically when the browser is closed.
    SESSION_USE_SIGNER = True # Ensure session cookies are signed for security.
    # Define a directory to store session files.
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flask_session_data')

    # --- IP Whitelist Configuration ---
    IP_WHITELIST_ENABLED = os.getenv('IP_WHITELIST_ENABLED', 'False').lower() == 'true'
    IP_WHITELIST = [ip.strip() for ip in os.getenv('IP_WHITELIST', '').split(',') if ip.strip()]

    # --- Admin Credentials (for initial setup or recovery) ---
    # These should ideally also come from environment variables for production.
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpass') # PLEASE CHANGE IN PRODUCTION!
    ADMIN_RECOVERY_KEY = os.getenv('ADMIN_RECOVERY_KEY', 'recovery123') # PLEASE CHANGE IN PRODUCTION!

    # --- SQLALCHEMY_DATABASE_URI can also be set here, but we put it in app.py for clarity. ---
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
