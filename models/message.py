# models/message.py
from app import db # Import the SQLAlchemy db instance from app.py
from datetime import datetime
import uuid # Import uuid for generating unique IDs for primary keys

class Message(db.Model):
    # Define the table name for this model
    __tablename__ = 'messages'

    # Define columns for the 'messages' table
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # UUID as primary key
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False) # Foreign key to Chat table
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False) # Foreign key to User table
    content = db.Column(db.Text, nullable=False) # Encrypted message content
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted_by_user = db.Column(db.Boolean, default=False) # Soft delete for user view
    is_permanently_deleted = db.Column(db.Boolean, default=False) # Hard delete for admin recovery

    # Relationships to other models (optional, for easier access)
    sender = db.relationship('User', backref='sent_messages', lazy=True) # Message has one sender (User)

    def __repr__(self):
        # String representation for debugging
        return f'<Message {self.id} from {self.sender_id} in chat {self.chat_id}>'

    # Method to save (add or update) message to the database
    def save(self):
        db.session.add(self)
        db.session.commit()

    # Method to delete message from the database
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Static method to get messages for a specific chat, ordered by timestamp
    @staticmethod
    def get_messages_for_chat(chat_id):
        return Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
