import pytest
from app import app, db, User
from flask_login import current_user

@pytest.fixture
def client():
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["LOGIN_DISABLED"] = False # Enable login for auth tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_register_login_flow(client):
    """Test standard auth flow."""
    # 1. Register
    resp = client.post("/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"testuser" in resp.data # Should show username in header
    
    # 2. Logout
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Login" in resp.data
    
    # 3. Login
    resp = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"testuser" in resp.data

def test_login_fail(client):
    """Test invalid credentials."""
    resp = client.post("/login", data={
        "email": "wrong@example.com",
        "password": "wrong"
    }, follow_redirects=True)
    assert b"Please check your login details" in resp.data

def test_register_duplicate(client):
    """Test duplicate email registration."""
    # Create user directly
    u = User(username="u1", email="exist@example.com")
    u.set_password("p")
    with app.app_context():
        db.session.add(u)
        db.session.commit()
        
    resp = client.post("/register", data={
        "username": "u2",
        "email": "exist@example.com",
        "password": "p"
    }, follow_redirects=True)
    assert b"Email address already exists" in resp.data
