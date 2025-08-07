import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail
from crypto_utils import CryptoUtils
from identity_verifier import IdentityVerifier

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)

# In-memory storage for MVP
users = {}  # {user_id: {email, password_hash, public_key, private_key, verified, created_at}}
messages = {}  # {message_id: {sender_id, recipient_id, encrypted_content, sent_at}}
verification_codes = {}  # {email: {code, expires_at}}
user_sessions = {}  # {session_id: user_id}

crypto_utils = CryptoUtils()
identity_verifier = IdentityVerifier(mail)

def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session and session['user_id'] in users:
        return users[session['user_id']]
    return None

def require_login(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


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
        
        # Check if email already exists
        for user_data in users.values():
            if user_data['email'] == email:
                flash('Email already registered. Please log in.', 'warning')
                return redirect(url_for('login'))
        
        try:
            # Generate RSA key pair
            public_key, private_key = crypto_utils.generate_key_pair()
            
            # Create user
            user_id = f"user_{len(users) + 1}"
            users[user_id] = {
                'email': email,
                'password_hash': crypto_utils.hash_password(password),
                'public_key': public_key,
                'private_key': private_key,
                'verified': True,
                'created_at': datetime.now()
            }
            
            # Registration successful
            flash('Registration successful! You can now start sending encrypted messages.', 'success')
            session['user_id'] = user_id
            return redirect(url_for('dashboard'))
                
        except Exception as e:
            logging.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
    
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
        
        # Find user by email
        user_id = None
        for uid, user_data in users.items():
            if user_data['email'] == email:
                user_id = uid
                break
        
        if user_id and crypto_utils.verify_password(password, users[user_id]['password_hash']):
            session['user_id'] = user_id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@require_login
def dashboard():
    """User dashboard"""
    user = get_current_user()
    
    # Get recent messages for this user
    user_messages = []
    for msg_id, msg_data in messages.items():
        if msg_data['recipient_id'] == session['user_id'] or msg_data['sender_id'] == session['user_id']:
            user_messages.append({
                'id': msg_id,
                'sender_email': users[msg_data['sender_id']]['email'],
                'recipient_email': users[msg_data['recipient_id']]['email'],
                'sent_at': msg_data['sent_at'],
                'is_sent': msg_data['sender_id'] == session['user_id']
            })
    
    # Sort by most recent
    user_messages.sort(key=lambda x: x['sent_at'], reverse=True)
    user_messages = user_messages[:10]  # Show last 10 messages
    
    return render_template('dashboard.html', user=user, recent_messages=user_messages)

@app.route('/send-message', methods=['GET', 'POST'])
@require_login
def send_message():
    """Send encrypted message"""
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email', '').strip().lower()
        message_content = request.form.get('message', '').strip()
        
        if not recipient_email or not message_content:
            flash('Recipient email and message content are required.', 'danger')
            return render_template('send_message.html')
        
        # Find recipient
        recipient_id = None
        for uid, user_data in users.items():
            if user_data['email'] == recipient_email:
                recipient_id = uid
                break
        
        if not recipient_id:
            flash('Recipient not found.', 'danger')
            return render_template('send_message.html')
        
        if recipient_id == session['user_id']:
            flash('You cannot send a message to yourself.', 'warning')
            return render_template('send_message.html')
        
        try:
            # Encrypt message with recipient's public key
            recipient_public_key = users[recipient_id]['public_key']
            encrypted_content = crypto_utils.encrypt_message(message_content, recipient_public_key)
            
            # Store message
            message_id = f"msg_{len(messages) + 1}"
            messages[message_id] = {
                'sender_id': session['user_id'],
                'recipient_id': recipient_id,
                'encrypted_content': encrypted_content,
                'sent_at': datetime.now()
            }
            
            flash('Message sent successfully!', 'success')
            return redirect(url_for('messages_view'))
            
        except Exception as e:
            logging.error(f"Message encryption error: {str(e)}")
            flash('Failed to send message. Please try again.', 'danger')
    
    return render_template('send_message.html')

@app.route('/messages')
@require_login
def messages_view():
    """View all messages"""
    user_id = session['user_id']
    user_private_key = users[user_id]['private_key']
    
    # Get all messages for this user
    user_messages = []
    for msg_id, msg_data in messages.items():
        if msg_data['recipient_id'] == user_id or msg_data['sender_id'] == user_id:
            message_info = {
                'id': msg_id,
                'sender_email': users[msg_data['sender_id']]['email'],
                'recipient_email': users[msg_data['recipient_id']]['email'],
                'sent_at': msg_data['sent_at'],
                'is_sent': msg_data['sender_id'] == user_id,
                'decrypted_content': None,
                'decryption_error': None
            }
            
            # Try to decrypt if this user is the recipient
            if msg_data['recipient_id'] == user_id:
                try:
                    message_info['decrypted_content'] = crypto_utils.decrypt_message(
                        msg_data['encrypted_content'], user_private_key
                    )
                except Exception as e:
                    message_info['decryption_error'] = str(e)
                    logging.error(f"Message decryption error: {str(e)}")
            
            user_messages.append(message_info)
    
    # Sort by most recent
    user_messages.sort(key=lambda x: x['sent_at'], reverse=True)
    
    return render_template('messages.html', messages=user_messages)

@app.route('/users')
@require_login
def users_list():
    """List all verified users for messaging"""
    current_user_id = session['user_id']
    all_users = []
    
    for uid, user_data in users.items():
        if uid != current_user_id:
            all_users.append({
                'id': uid,
                'email': user_data['email'],
                'created_at': user_data['created_at']
            })
    
    all_users.sort(key=lambda x: x['email'])
    
    return render_template('users.html', users=all_users)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
