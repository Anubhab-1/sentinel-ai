from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from database import User, db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        return redirect(url_for('index'))
        
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Invalid email address.', 'error')
            return redirect(url_for('auth.register'))
            
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'error')
            return redirect(url_for('auth.register'))
            
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user) # Auto login after register
        return redirect(url_for('index'))
        
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- OTP & Password Reset Logic ---
import random
import string
from flask_mail import Message
from app import mail, redis_client

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, otp):
    try:
        msg = Message("Sentinel AI - Verification Code", recipients=[to_email])
        msg.body = f"Your verification code is: {otp}\n\nThis code expires in 5 minutes."
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Error: {e}")
        return False

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('If an account exists, an email has been sent.', 'info')
            return redirect(url_for('auth.login'))
        
        # Generate & Send
        otp = generate_otp()
        redis_client.setex(f"otp:{email}", 300, otp) # 5 mins
        
        if send_otp_email(email, otp):
            flash('OTP sent to your email.', 'success')
            return redirect(url_for('auth.verify_otp', email=email))
        else:
            flash('Error sending email. Check logs.', 'error')
            
    return render_template('forgot_password.html')

@auth.route('/verify-otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        code = request.form.get('otp')
        stored = redis_client.get(f"otp:{email}")
        
        if stored and stored.decode('utf-8') == code:
            # Verified! clear OTP and allow reset
            redis_client.delete(f"otp:{email}")
            # Generate a temporary reset token (single use)
            token = generate_otp() # Reusing simple number for simplicity
            redis_client.setex(f"reset:{email}", 300, token)
            return redirect(url_for('auth.reset_password', email=email, token=token))
        
        flash('Invalid or Expired OTP.', 'error')
        
    return render_template('verify_otp.html', email=email)

@auth.route('/reset-password/<email>/<token>', methods=['GET', 'POST'])
def reset_password(email, token):
    stored = redis_client.get(f"reset:{email}")
    if not stored or stored.decode('utf-8') != token:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            redis_client.delete(f"reset:{email}") # Burn token
            flash('Password reset successfully. Please login.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('reset_password.html')
