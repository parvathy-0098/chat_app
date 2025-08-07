import os
import logging
import uuid
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail
from models import db, User, Message, VerificationCode
from crypto_utils import CryptoUtils
from identity_verifier import IdentityVerifier

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Initialize services
crypto_utils = CryptoUtils()
identity_verifier = IdentityVerifier(mail)

def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def get_unread_count(user_id):
    """Get unread message count for user"""
    return Message.query.filter_by(recipient_id=user_id, read_at=None).count()

def require_login(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.context_processor
def inject_unread_count():
    """Inject unread message count into all templates"""
    user = get_current_user()
    if user:
        unread_count = get_unread_count(user.id)
        return dict(unread_count=unread_count)
    return dict(unread_count=0)

@app.route('/')
def index():
    """Homepage"""
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(email=email)
        user.set_password(password)
        user.verified = True  # Auto-verify for simplified flow
        
        try:
            # Generate RSA keys immediately
            public_key, private_key = crypto_utils.generate_key_pair()
            user.public_key = public_key
            user.private_key = private_key
            
            db.session.add(user)
            db.session.commit()
            
            # Auto-login the user
            session['user_id'] = user.id
            
            # Send welcome messages from test users
            try:
                test_users = User.query.filter(User.email.like('%test%')).all()
                welcome_messages = [
                    {'sender_email': 'alice@test.com', 'content': f'Welcome to SecureChat, {email}! I\'m Alice. Feel free to send me a message!'},
                    {'sender_email': 'bob@test.com', 'content': f'Hi {email}! Bob here. Great to have you on SecureChat!'},
                    {'sender_email': 'charlie@test.com', 'content': f'Hello {email}! Welcome from Charlie. Looking forward to chatting!'}
                ]
                
                for msg_data in welcome_messages:
                    sender = User.query.filter_by(email=msg_data['sender_email']).first()
                    if sender and sender.public_key:
                        encrypted_content = crypto_utils.encrypt_message(msg_data['content'], user.public_key)
                        welcome_msg = Message(
                            sender_id=sender.id,
                            recipient_id=user.id,
                            encrypted_content=encrypted_content
                        )
                        db.session.add(welcome_msg)
                
                db.session.commit()
                flash('Registration successful! Your account is ready and encryption keys have been generated. You have new welcome messages!', 'success')
            except Exception as e:
                logging.error(f"Error sending welcome messages: {str(e)}")
                flash('Registration successful! Your account is ready and encryption keys have been generated.', 'success')
            
            return redirect(url_for('messages_view'))
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('messages_view'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@require_login
def dashboard():
    """User dashboard"""
    user = get_current_user()
    
    # Get recent messages
    recent_messages = Message.query.filter_by(recipient_id=user.id).order_by(Message.sent_at.desc()).limit(5).all()
    
    # Get message counts
    unread_count = Message.query.filter_by(recipient_id=user.id, read_at=None).count()
    total_sent = Message.query.filter_by(sender_id=user.id).count()
    total_received = Message.query.filter_by(recipient_id=user.id).count()
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_messages=recent_messages,
                         unread_count=unread_count,
                         total_sent=total_sent,
                         total_received=total_received)

@app.route('/send-message', methods=['GET', 'POST'])
@require_login
def send_message():
    """Send encrypted message"""
    current_user = get_current_user()
    
    # Get list of available users for suggestions
    available_users = User.query.filter(
        User.verified == True,
        User.id != current_user.id,
        User.public_key.isnot(None)
    ).order_by(User.email).all()
    
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email', '').strip().lower()
        message_content = request.form.get('message_content', '').strip()
        
        if not recipient_email or not message_content:
            flash('Recipient email and message content are required.', 'danger')
            return render_template('send_message.html')
        
        # Find recipient
        recipient = User.query.filter_by(email=recipient_email, verified=True).first()
        if not recipient:
            flash('Recipient not found or not verified.', 'danger')
            return render_template('send_message.html')
        
        if recipient.id == current_user.id:
            flash('You cannot send a message to yourself.', 'warning')
            return render_template('send_message.html')
        
        if not recipient.public_key:
            flash('Recipient does not have encryption keys set up.', 'danger')
            return render_template('send_message.html')
        
        try:
            # Encrypt message
            encrypted_content = crypto_utils.encrypt_message(message_content, recipient.public_key)
            
            # Save message
            message = Message(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                encrypted_content=encrypted_content
            )
            db.session.add(message)
            db.session.commit()
            
            flash(f'Message sent successfully to {recipient_email}!', 'success')
            return redirect(url_for('messages_view'))
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            flash('Failed to send message. Please try again.', 'danger')
    
    return render_template('send_message.html', available_users=available_users)

@app.route('/messages')
@require_login
def messages_view():
    """View messages"""
    current_user = get_current_user()
    
    # Get received messages
    received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.sent_at.desc()).all()
    
    # Get sent messages
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.sent_at.desc()).all()
    
    # Decrypt received messages
    decrypted_received = []
    for msg in received_messages:
        try:
            decrypted_content = crypto_utils.decrypt_message(msg.encrypted_content, current_user.private_key)
            decrypted_received.append({
                'message': msg,
                'decrypted_content': decrypted_content,
                'sender_email': msg.sender.email
            })
        except Exception as e:
            logging.error(f"Error decrypting message {msg.id}: {str(e)}")
            decrypted_received.append({
                'message': msg,
                'decrypted_content': '[Error decrypting message]',
                'sender_email': msg.sender.email
            })
    
    return render_template('messages.html', 
                         received_messages=decrypted_received,
                         sent_messages=sent_messages,
                         current_user=current_user)

@app.route('/message/<int:message_id>/mark-read', methods=['POST'])
@require_login
def mark_message_read(message_id):
    """Mark message as read"""
    current_user = get_current_user()
    message = Message.query.filter_by(id=message_id, recipient_id=current_user.id).first()
    
    if message:
        message.mark_as_read()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@app.route('/users')
@require_login
def users_list():
    """List all verified users"""
    current_user = get_current_user()
    
    # Get all verified users except current user
    all_users = User.query.filter(
        User.verified == True,
        User.id != current_user.id
    ).order_by(User.email).all()
    
    users_data = []
    for user in all_users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'created_at': user.created_at,
            'has_keys': bool(user.public_key)
        })
    
    return render_template('users.html', users=users_data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logging.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

def seed_test_data():
    """Seed database with test users and messages"""
    try:
        # Check if we already have test data
        existing_users = User.query.filter(User.email.like('%test%')).count()
        if existing_users >= 3:
            return  # Test data already exists
        
        # Create test users
        test_users = [
            {'email': 'alice@test.com', 'password': 'password123'},
            {'email': 'bob@test.com', 'password': 'password123'},
            {'email': 'charlie@test.com', 'password': 'password123'}
        ]
        
        created_users = []
        for user_data in test_users:
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(email=user_data['email'])
                user.set_password(user_data['password'])
                user.verified = True
                
                # Generate RSA keys
                public_key, private_key = crypto_utils.generate_key_pair()
                user.public_key = public_key
                user.private_key = private_key
                
                db.session.add(user)
                created_users.append(user)
        
        db.session.commit()
        
        # Create sample messages if we have created users
        if created_users and len(created_users) >= 3:
            alice, bob, charlie = created_users[0], created_users[1], created_users[2]
            
            sample_messages = [
                {'sender': alice, 'recipient': bob, 'content': 'Hello Bob! How are you doing today?'},
                {'sender': bob, 'recipient': alice, 'content': 'Hi Alice! I\'m doing great, thanks for asking. How about you?'},
                {'sender': charlie, 'recipient': alice, 'content': 'Hey Alice, do you want to join our project meeting tomorrow?'},
                {'sender': alice, 'recipient': charlie, 'content': 'Sure Charlie! What time is the meeting?'},
                {'sender': bob, 'recipient': charlie, 'content': 'Charlie, don\'t forget about our lunch plans on Friday!'},
                {'sender': charlie, 'recipient': bob, 'content': 'Thanks for the reminder Bob! Looking forward to it.'}
            ]
            
            for msg_data in sample_messages:
                try:
                    encrypted_content = crypto_utils.encrypt_message(msg_data['content'], msg_data['recipient'].public_key)
                    message = Message(
                        sender_id=msg_data['sender'].id,
                        recipient_id=msg_data['recipient'].id,
                        encrypted_content=encrypted_content,
                        sent_at=datetime.utcnow() - timedelta(minutes=30)  # 30 minutes ago
                    )
                    db.session.add(message)
                except Exception as e:
                    logging.error(f"Error creating sample message: {str(e)}")
            
            db.session.commit()
            logging.info(f"Created {len(created_users)} test users and {len(sample_messages)} sample messages")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding test data: {str(e)}")

# Create tables and seed test data
with app.app_context():
    db.create_all()
    
    # Seed test data
    seed_test_data()
    
    # Clean up expired verification codes on startup
    try:
        expired_count = VerificationCode.cleanup_expired()
        if expired_count > 0:
            logging.info(f"Cleaned up {expired_count} expired verification codes")
    except Exception as e:
        logging.error(f"Error cleaning up expired codes: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)