# utils/security_utils.py
from flask import request, abort, flash, redirect, url_for, session
from datetime import datetime, timedelta
from app import app # Import app to access app.config

def check_ip_whitelist():
    """Checks if the client's IP is whitelisted."""
    if not app.config['IP_WHITELIST_ENABLED']:
        return True
    client_ip = request.remote_addr
    if client_ip not in app.config['IP_WHITELIST']:
        return False
    return True

def login_required(f):
    """Decorator to ensure user is logged in."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to be logged in to access this page.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Implement tamper detection (conceptual)
def check_for_tampering():
    """
    Conceptual function for tamper detection.
    This could involve:
    1. Checking file hashes of critical application files on startup.
    2. Monitoring database schema changes (more complex for MongoDB).
    3. Detecting unusual access patterns (requires logging and analysis).
    """
    # Example: Check hash of app.py on startup
    # hash_file('app.py') and compare to a stored hash.
    # If tamper detected:
    # app.logger.error("TAMPERING DETECTED! Shutting down server.")
    # abort(500, "System Integrity Compromised.") # Or more graceful shutdown
    pass # To be implemented later

# This function might be called at app startup or periodically.