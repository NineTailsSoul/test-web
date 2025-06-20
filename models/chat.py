# models/chat.py
from app import db # Import the SQLAlchemy db instance from app.py
from datetime import datetime
import uuid # Import uuid for generating unique IDs for primary keys

# Association table for many-to-many relationship between Chat and User
# This table links chats to their participants without a separate model class.
chat_participants = db.Table('chat_participants',
    db.Column('chat_id', db.String(36), db.ForeignKey('chats.id'), primary_key=True),
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True)
)

class Chat(db.Model):
    # Define the table name for this model
    __tablename__ = 'chats'

    # Define columns for the 'chats' table
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # UUID as primary key
    name = db.Column(db.String(120), nullable=True) # For group chats, null for 1-1 chats
    is_group_chat = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationship to User model using the association table (chat_participants)
    # 'participants' attribute on Chat will return a list of User objects
    participants = db.relationship('User', secondary=chat_participants, lazy='subquery',
                                   backref=db.backref('chats', lazy=True)) # 'chats' backref on User model

    # Relationship to Message model: one-to-many (one chat can have many messages)
    # 'cascade="all, delete-orphan"' ensures messages are deleted if their parent chat is deleted
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        # String representation for debugging
        return f'<Chat {self.id} - {self.name if self.name else "Direct Chat"}>'

    # Method to save (add or update) chat to the database
    def save(self):
        db.session.add(self)
        db.session.commit()

    # Method to delete chat from the database (and associated messages due to cascade)
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Static method to find a chat by its ID (primary key)
    @staticmethod
    def find_by_id(chat_id):
        return Chat.query.get(chat_id)

    # Static method to find a direct (non-group) chat between two specific users
    @staticmethod
    def find_direct_chat(user1_id, user2_id):
        # This query looks for a non-group chat that has exactly two participants
        # and those participants are the two specified users.
        chat = db.session.query(Chat).\
            join(chat_participants).\
            filter(Chat.is_group_chat == False).\
            group_by(Chat.id).\
            having(db.func.count(chat_participants.c.user_id) == 2).\
            filter(chat_participants.c.user_id.in_([user1_id, user2_id])).\
            first()
        return chat

    # Static method to get all chats for a specific user
    @staticmethod
    def get_user_chats(user_id):
        # This fetches a user and then accesses their associated chats through the relationship
        user = db.session.query(db.models.User).options(db.joinedload(db.models.User.chats)).filter_by(id=user_id).first()
        if user:
            return user.chats
        return []
