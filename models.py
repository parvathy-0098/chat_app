from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    public_key = db.Column(db.Text, nullable=True)
    private_key = db.Column(db.Text, nullable=True)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'verified': self.verified,
            'created_at': self.created_at.isoformat(),
            'has_keys': bool(self.public_key and self.private_key)
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encrypted_content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_recipient_sent', recipient_id, sent_at.desc()),
        db.Index('idx_sender_sent', sender_id, sent_at.desc()),
    )
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.read_at:
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        sender_user = User.query.get(self.sender_id)
        recipient_user = User.query.get(self.recipient_id)
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_email': sender_user.email if sender_user else 'Unknown',
            'recipient_id': self.recipient_id,
            'recipient_email': recipient_user.email if recipient_user else 'Unknown',
            'encrypted_content': self.encrypted_content,
            'sent_at': self.sent_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': bool(self.read_at)
        }

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired verification codes"""
        expired_codes = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for code in expired_codes:
            db.session.delete(code)
        db.session.commit()
        return len(expired_codes)
    
    def is_valid(self):
        """Check if code is still valid"""
        return not self.used and self.expires_at > datetime.utcnow()
    
    def use_code(self):
        """Mark code as used"""
        self.used = True
        db.session.commit()