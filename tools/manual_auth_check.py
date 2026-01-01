import os
os.environ['DATABASE_URL']='sqlite:///:memory:'
os.environ['MAIL_SERVER']='localhost'

from app import app
from database import db

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as c:
    with app.app_context():
        db.create_all()
        # Register
        resp = c.post('/register', data={'username':'tuser','email':'test@example.com','password':'pass'}, follow_redirects=False)
        print('register status', resp.status_code, 'Location:', resp.headers.get('Location'))
        if resp.status_code in (301,302):
            # follow once
            resp2 = c.get(resp.headers['Location'], follow_redirects=True)
            print('after redirect, contains username?', b'tuser' in resp2.data)
            print('flash messages page contains invalid email?', b'Invalid email address' in resp2.data)
        else:
            print('no redirect, body snippet:', resp.data[:400])
        from database import User
        all_u = User.query.all()
        print('all users count:', len(all_u), [(x.username, x.email, hasattr(x,'password_hash')) for x in all_u])
        u = User.query.filter_by(email='t@example.com').first()
        if u:
            print('user password_hash present?', bool(u.password_hash))
        print('user exists after register:', bool(u), u.username if u else None)
        # Logout
        resp = c.get('/logout', follow_redirects=True)
        print('logout status', resp.status_code, b'Login' in resp.data)
        # Login
        resp = c.post('/login', data={'email':'t@example.com','password':'pass'}, follow_redirects=True)
        print('login status', resp.status_code)
        print('login response snippet:', resp.data[:400])
        print('contains username?', b'tuser' in resp.data)
        # Wrong login
        resp = c.post('/login', data={'email':'wrong','password':'x'}, follow_redirects=True)
        print('wrong login contains message', b'Please check your login details' in resp.data)
