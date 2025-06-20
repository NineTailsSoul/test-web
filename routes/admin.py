# routes/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.user import User
from models.message import Message
from models.chat import Chat # <-- YE LINE ADD KARO
# from app import db # <-- YE LINE HATA DO
from bson.objectid import ObjectId
admin_bp = Blueprint('admin', __name__)
# Admin access decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    all_users = User.get_all_users()
    deleted_messages = Message.get_deleted_messages_for_admin()
    # Format messages for display in admin panel
    formatted_deleted_messages = []
    for msg in deleted_messages:
        sender = User.find_by_id(str(msg['sender_id']))
        # chat = db.chats.find_one({"_id": msg['chat_id']}) # <-- YE LINE HATA DO
        chat = Chat.collection.find_one({"_id": msg['chat_id']}) # <-- YE LINE USE KARO
        chat_participants = []
        if chat:
            for p_id in chat['participants']:
                p_user = User.find_by_id(str(p_id))
                if p_user:
                    chat_participants.append(p_user['username'])
        formatted_deleted_messages.append({
            'id': str(msg['_id']),
            'sender_username': sender['username'] if sender else 'Unknown',
            'content': msg['content'], # Still encrypted, admin won't decrypt here
            'timestamp': msg['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            'chat_participants': ", ".join(chat_participants)
        })
    return render_template('admin/dashboard.html', users=all_users, deleted_messages=formatted_deleted_messages)
@admin_bp.route('/admin/toggle_admin/<user_id>', methods=['POST'])
@admin_required
def toggle_admin_status(user_id):
    # ... (rest of the code is fine) ...
    pass
@admin_bp.route('/admin/recover_message/<message_id>', methods=['POST'])
@admin_required
def recover_message(message_id):
    # ... (rest of the code is fine) ...
    pass
@admin_bp.route('/admin/permanent_delete_message/<message_id>', methods=['POST'])
@admin_required
def permanent_delete_message(message_id):
    # ... (rest of the code is fine) ...
    pass
@admin_bp.route('/admin/delete_user/<user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    from bson.objectid import ObjectId
    user_obj_id = ObjectId(user_id)
    user_to_delete = User.find_by_id(user_id)
    if user_to_delete and str(user_to_delete['_id']) != session['user_id']: # Prevent admin from deleting self
        User.collection.delete_one({"_id": user_obj_id})
        # Also delete all messages and chats associated with this user
        # db.messages.delete_many({"$or": [{"sender_id": user_obj_id}, {"recipient_id": user_obj_id}]}) # <-- YE LINE HATA DO
        Message.collection.delete_many({"$or": [{"sender_id": user_obj_id}, {"recipient_id": user_obj_id}]}) # <-- YE LINE USE KARO
        # db.chats.delete_many({"participants": user_obj_id}) # <-- YE LINE HATA DO
        Chat.collection.delete_many({"participants": user_obj_id}) # <-- YE LINE USE KARO
        flash(f"User {user_to_delete['username']} and associated data deleted.", "success")
    else:
        flash("Could not delete user or cannot delete yourself.", "danger")
    return redirect(url_for('admin.dashboard'))
