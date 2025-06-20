# routes/chat.py
from flask import Blueprint, render_template, session, request, jsonify, flash
from models.chat import Chat
from models.user import User
from models.message import Message
from bson.objectid import ObjectId

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/home')
def home():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your chats.", "danger")
        return redirect(url_for('auth.login'))

    user = User.find_by_id(user_id)
    if not user:
        session.clear()
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    # Get user's friend list and convert usernames to user objects for display
    friend_usernames = user.get('friends', [])
    friends = [User.find_by_username(f_username) for f_username in friend_usernames if User.find_by_username(f_username)]

    # Get all chats the user is part of
    user_chats = Chat.get_user_chats(user_id)
    chats_with_details = []
    for chat in user_chats:
        other_participants = [
            User.find_by_id(str(p_id)) for p_id in chat['participants'] if str(p_id) != user_id
        ]
        # For 1-on-1 chats, the 'chat_name' will be the other person's username
        chat_name = ", ".join([p['username'] for p in other_participants if p])
        if not chat_name: # Handle case where only one participant (self-chat or error)
            chat_name = "Unknown Chat"
        
        # Get last message for preview
        last_message = Message.collection.find(
            {"chat_id": chat['_id'], "is_deleted_by_user": False}
        ).sort("timestamp", -1).limit(1)
        last_message_content = "No messages yet."
        if last_message and last_message.count() > 0: # Check if cursor has items
            last_msg_doc = last_message[0]
            last_message_content = f"Last message from {User.find_by_id(str(last_msg_doc['sender_id']))['username']}: (Encrypted)" # Placeholder for encrypted content

        chats_with_details.append({
            '_id': str(chat['_id']),
            'name': chat_name,
            'participants': [{'id': str(p_id), 'username': User.find_by_id(str(p_id))['username']} for p_id in chat['participants']],
            'last_message_preview': last_message_content
        })

    return render_template('chat/index.html', current_user=user, friends=friends, chats=chats_with_details)

@chat_bp.route('/get_messages/<chat_id>', methods=['GET'])
def get_messages(chat_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Basic check: Ensure user is a participant of this chat
    chat = Chat.collection.find_one({"_id": ObjectId(chat_id), "participants": ObjectId(user_id)})
    if not chat:
        return jsonify({"error": "Chat not found or you are not a participant"}), 403

    messages_data = Message.get_messages_for_chat(chat_id)
    
    # Format messages for frontend (no decryption here, it's client-side)
    formatted_messages = []
    for msg in messages_data:
        sender = User.find_by_id(str(msg['sender_id']))
        formatted_messages.append({
            'id': str(msg['_id']),
            'sender_id': str(msg['sender_id']),
            'sender_username': sender['username'] if sender else 'Unknown',
            'content': msg['content'], # Still encrypted
            'timestamp': msg['timestamp'].isoformat(),
            'is_self': str(msg['sender_id']) == user_id
        })
    return jsonify(formatted_messages)

@chat_bp.route('/delete_message/<message_id>', methods=['POST'])
def delete_message(message_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if Message.delete_message_by_user(message_id, user_id):
        return jsonify({"success": True, "message": "Message deleted."}), 200
    return jsonify({"success": False, "message": "Failed to delete message."}), 400

@chat_bp.route('/start_chat_with_friend/<friend_username>', methods=['POST'])
def start_chat_with_friend(friend_username):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    current_user_obj = User.find_by_id(user_id)
    friend_user_obj = User.find_by_username(friend_username)

    if not current_user_obj or not friend_user_obj:
        return jsonify({"error": "User or friend not found."}), 404

    # Ensure they are friends
    if friend_username not in current_user_obj.get('friends', []):
        return jsonify({"error": "You are not friends with this user."}), 403

    # Create or find chat between these two users
    chat_id, created = Chat.create_chat([str(current_user_obj['_id']), str(friend_user_obj['_id'])])
    
    return jsonify({"success": True, "chat_id": str(chat_id)})