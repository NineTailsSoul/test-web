# app.py

from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy # Import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for SECRET_KEY etc.)
load_dotenv()

# --- Initialize Flask app ---
app = Flask(__name__)

# --- Load configuration from config.py ---
# This must happen before SQLAlchemy initialization if Config sets SQLALCHEMY_DATABASE_URI
from config import Config
app.config.from_object(Config)

# --- SQLAlchemy Configuration for SQLite ---
# SQLite database file will be created in the project root
# This line can also be in Config class, but placing it here explicitly
# confirms its setting AFTER Config is loaded.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable tracking modifications to save memory

# --- Initialize Flask-SQLAlchemy DB INSTANCE FIRST ---
# This is CRUCIAL to fix the circular import.
# The 'db' object MUST be ready before models try to import it.
db = SQLAlchemy(app)

# --- Initialize Flask-Session (using 'filesystem' as set in config.py) ---
server_session = Session(app)

# Initialize SocketIO
socketio = SocketIO(app, manage_session=False, async_mode='eventlet', cors_allowed_origins="*")

# --- NOW, IMPORT MODELS (AFTER 'db' IS READY) ---
# Models will now be SQLAlchemy models, they will use the 'db' object from app.py
from models.user import User
from models.chat import Chat
from models.message import Message

# --- Create Database Tables ---
# This line will create all tables defined in your models based on SQLAlchemy.
# It should run only once when the app starts, or when you modify models.
# For local testing, this will create 'site.db' in your project workspace.
with app.app_context():
    db.create_all()


# --- Register Blueprints (IMPORT ROUTES HERE, AFTER MODELS ARE READY) ---
# Blueprints should be imported after models so models are available to routes.
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.contacts import contacts_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(contacts_bp, url_prefix='/contacts')
app.register_blueprint(admin_bp, url_prefix='/admin')

# --- Utility Functions (Place in utils/security_utils.py later) ---
def is_ip_whitelisted():
    # Implement actual IP whitelisting logic based on your environment.
    # For local testing, you might want to return True unless specifically testing this feature.
    if not app.config['IP_WHITELIST_ENABLED']:
        return True
    client_ip = request.remote_addr # Get the client's IP address
    return client_ip in app.config['IP_WHITELIST']


# --- BEFORE REQUEST HOOKS ---
@app.before_request
def check_ip_whitelist():
    # Check IP whitelist for all routes except static files, login, and registration.
    if app.config['IP_WHITELIST_ENABLED'] and \
       not is_ip_whitelisted() and \
       request.endpoint not in ['static', 'auth.login', 'auth.register']:
        return "Access Denied: Your IP address is not whitelisted.", 403

@app.before_request
def enforce_login():
    # Ensure user is logged in for protected routes.
    allowed_routes = ['auth.login', 'auth.register', 'static', 'index'] # 'index' is the root route
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        flash("You need to be logged in to access this page.", "danger")
        return redirect(url_for('auth.login'))

@app.route('/')
def index():
    # Root route: Redirect to chat.home if logged in, otherwise show login page.
    if 'user_id' in session:
        return redirect(url_for('chat.home'))
    return render_template('auth/login.html')

# --- SocketIO Events (These can be moved to routes/chat.py or a separate socket_events.py later) ---
@socketio.on('connect')
def handle_connect():
    # Handle client connection
    if 'user_id' not in session:
        print(f"Unauthorized connect attempt from {request.sid}")
        return False # Deny connection if user is not authenticated
    print(f"Client connected: {request.sid} for user: {session.get('username')}")
    emit('status', {'msg': 'Connected to StealthComm server'})

@socketio.on('disconnect')
def handle_disconnect():
    # Handle client disconnection
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_chat')
def on_join_chat(data):
    # User joins a specific chat room (SocketIO room)
    if 'user_id' not in session:
        return # Unauthorized
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        print(f"User {session.get('username')} joined room {room_id}")
        emit('status', {'msg': f'You have joined chat {room_id}'}, room=request.sid)

@socketio.on('leave_chat')
def on_leave_chat(data):
    # User leaves a specific chat room
    if 'user_id' not in session:
        return # Unauthorized
    room_id = data.get('room_id')
    if room_id:
        leave_room(room_id)
        print(f"User {session.get('username')} left room {room_id}")
        emit('status', {'msg': f'You have left chat {room_id}'}, room=request.sid)

@socketio.on('send_message')
def handle_message(data):
    # Handle sending of encrypted messages
    if 'user_id' not in session:
        return # Unauthorized

    sender_id = session['user_id']
    chat_id = data.get('chat_id')
    encrypted_message = data.get('message') # This should be the AES-256 encrypted message from client

    if not chat_id or not encrypted_message:
        return # Invalid data

    # Create new message using SQLAlchemy model and save to DB
    new_message_obj = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=encrypted_message,
        timestamp=datetime.utcnow(),
        is_deleted_by_user=False,
        is_permanently_deleted=False
    )
    db.session.add(new_message_obj)
    db.session.commit() # Save message to the SQLite database

    # Emit message to the specific chat room
    emit('receive_message', {
        'chat_id': chat_id,
        'sender_id': sender_id,
        'message': encrypted_message, # Send the encrypted message
        'timestamp': new_message_obj.timestamp.isoformat() # Convert datetime object to ISO format string for frontend
    }, room=chat_id)
    print(f"Message sent to chat {chat_id} from {session.get('username')}")


@socketio.on('typing')
def handle_typing_indicator(data):
    # Handle typing indicators in chats
    if 'user_id' not in session:
        return
    chat_id = data.get('chat_id')
    is_typing = data.get('is_typing', False)
    if chat_id:
        # Emit typing status to others in the room, excluding the sender
        emit('typing_status', {'user_id': session['user_id'], 'username': session.get('username'), 'is_typing': is_typing}, room=chat_id, include_self=False)


# --- Run the app ---
if __name__ == '__main__':
    # Ensure database tables are created before running the app.
    # This will create 'site.db' in the project root if it doesn't exist.
    # It should only be run once for initial setup, but safe to keep here.
    with app.app_context():
        db.create_all()

    # Run the SocketIO app
    # 'PORT' environment variable is typically set by cloud environments (e.g., Codespaces)
    # Default to 5000 for local testing if PORT is not set.
    port = int(os.environ.get("PORT", 5000))
    host = '0.0.0.0' # Listen on all available network interfaces (for LAN/external access)
    socketio.run(app, debug=True, host=host, port=port)

