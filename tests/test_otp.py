import pytest
from app import app, db, redis_client
from database import User
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app.config["WTF_CSRF_ENABLED"] = False
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config["LOGIN_DISABLED"] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('oldpassword')
            db.session.add(user)
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()



@pytest.fixture
def mock_mail():
    with patch('auth.mail.send') as mock:
        yield mock




def test_forgot_password_flow(client, mock_mail, mock_redis):
    # 1. Request OTP
    response = client.post('/forgot-password', data={'email': 'test@example.com'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"OTP sent to your email" in response.data
    
    # Check if mail was "sent"
    assert mock_mail.called
    
    # 2. Get OTP from (Fake) Redis
    raw_otp = mock_redis.get('otp:test@example.com')
    assert raw_otp is not None
    otp_code = raw_otp.decode('utf-8')
    assert len(otp_code) == 6
    
    # 3. Verify OTP
    response = client.post(f'/verify-otp/test@example.com', data={'otp': otp_code}, follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to reset password page (contains "Set New Password")
    assert b"Set New Password" in response.data
    
    # 4. Check Reset Token in Redis
    token = mock_redis.get('reset:test@example.com').decode('utf-8')
    
    # 5. Reset Password
    response = client.post(f'/reset-password/test@example.com/{token}', data={'password': 'newpassword123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Password reset successfully" in response.data
    
    # 6. Verify Login with new password
    response = client.post('/login', data={'email': 'test@example.com', 'password': 'newpassword123'}, follow_redirects=True)
    assert b"Logout" in response.data
