# routes/contacts.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/add', methods=['GET', 'POST'])
def add_contact():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to manage contacts.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        friend_username = request.form['friend_username']
        if not friend_username:
            flash("Friend's username cannot be empty.", "danger")
            return redirect(url_for('contacts.add_contact'))

        if friend_username == session['username']:
            flash("You cannot add yourself as a friend.", "danger")
            return redirect(url_for('contacts.add_contact'))

        success, message = User.add_friend(user_id, friend_username)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
        return redirect(url_for('chat.home')) # Redirect to home to see updated friends list

    return render_template('contacts/add_contact.html')

@contacts_bp.route('/get_friends', methods=['GET'])
def get_friends():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    
    friend_usernames = user.get('friends', [])
    friends_data = []
    for f_username in friend_usernames:
        friend_user = User.find_by_username(f_username)
        if friend_user:
            friends_data.append({
                'id': str(friend_user['_id']),
                'username': friend_user['username']
            })
    return jsonify(friends_data)