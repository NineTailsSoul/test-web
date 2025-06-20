# models/user.py
from app import db # Import the SQLAlchemy db instance from app.py
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid # Import uuid for generating unique IDs for primary keys

class User(db.Model):
    # Define the table name for this model
    __tablename__ = 'users'

    # Define columns for the 'users' table
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # UUID as primary key
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    recovery_key = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), nullable=True) # To store last login IP
    public_key = db.Column(db.Text, nullable=True) # User's public key for encryption (e.g., RSA)
    private_key_encrypted = db.Column(db.Text, nullable=True) # User's encrypted private key

    def __repr__(self):
        # String representation for debugging
        return f'<User {self.username}>'

    def set_password(self, password):
        # Hashes the password for secure storage
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Checks a given password against the stored hash
        return check_password_hash(self.password_hash, password)

    # Method to save (add or update) user to the database
    def save(self):
        db.session.add(self)
        db.session.commit()

    # Method to delete user from the database
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Static method to find a user by username
    @staticmethod
    def find_by_username(username):
        return User.query.filter_by(username=username).first()

    # Static method to find a user by their ID (primary key)
    @staticmethod
    def find_by_id(user_id):
        return User.query.get(user_id) # get() is optimized for primary key lookup

    # Static method to retrieve all users (e.g., for admin panels or contact lists)
    @staticmethod
    def get_all_users():
        return User.query.all()

    # Admin authentication methods
    @staticmethod
    def authenticate_admin(username, password):
        user = User.query.filter_by(username=username, is_admin=True).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def recover_admin_account(username, recovery_key):
        user = User.query.filter_by(username=username, is_admin=True, recovery_key=recovery_key).first()
        return user
