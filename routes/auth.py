# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        login_password = request.form['login_password']
        chat_password = request.form['chat_password']

        if not username or not login_password or not chat_password:
            flash("All fields are required.", "danger")
            return render_template('auth/register.html')

        if User.find_by_username(username):
            flash("Username already exists.", "danger")
            return render_template('auth/register.html')

        try:
            User.create_user(username, login_password, chat_password)
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('auth/register.html')
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user, error = User.check_login_password(username, password)
        if user:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            flash("Logged in successfully!", "success")
            return redirect(url_for('chat.home'))
        else:
            flash(error, "danger")

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))