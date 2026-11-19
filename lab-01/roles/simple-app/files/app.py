#!/usr/bin/env python3
"""
Simple Flask Application with MariaDB integration
Deployed with Ansible + Gunicorn + Nginx
"""

from flask import Flask, jsonify, render_template_string, request
import socket
import datetime
import sys
import os
import config

app = Flask(__name__)

# Load configuration from config.py
app.config['APP_NAME'] = config.APP_NAME
app.config['ENVIRONMENT'] = config.ENVIRONMENT
app.config['DB_HOST'] = config.DB_HOST
app.config['DB_PORT'] = config.DB_PORT
app.config['DB_NAME'] = config.DB_NAME
app.config['DB_USER'] = config.DB_USER
app.config['DB_PASSWORD'] = config.DB_PASSWORD

HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__APP_NAME__ - Ansible Lab</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { font-size: 2.5em; margin-bottom: 20px; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .info-box { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 10px; margin: 15px 0; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2); }
        .info-box h3 { margin-bottom: 10px; color: #ffd700; }
        .status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
        .status.ok { background: #4caf50; }
        .status.error { background: #f44336; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.2); }
        td:first-child { font-weight: bold; width: 40%; color: #ffd700; }
        .user-form { background: rgba(255, 255, 255, 0.15); padding: 20px; border-radius: 10px; margin: 15px 0; }
        .user-form input { padding: 10px; margin: 5px; border-radius: 5px; border: none; width: calc(50% - 15px); }
        .user-form button { padding: 10px 20px; background: #4caf50; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .user-form button:hover { background: #45a049; }
        .users-list { background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 10px; margin: 15px 0; }
        .user-item { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2); display: flex; justify-content: space-between; }
        .footer { text-align: center; margin-top: 20px; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 __APP_NAME__</h1>
        
        <div class="info-box">
            <h3>📊 Server Information</h3>
            <table>
                <tr><td>Hostname:</td><td>__HOSTNAME__</td></tr>
                <tr><td>Python Version:</td><td>__PYTHON_VERSION__</td></tr>
                <tr><td>Flask Version:</td><td>__FLASK_VERSION__</td></tr>
                <tr><td>Server Time:</td><td>__SERVER_TIME__</td></tr>
                <tr><td>OS:</td><td>__OS_INFO__</td></tr>
                <tr><td>Uptime:</td><td>__UPTIME__</td></tr>
            </table>
        </div>

        <div class="info-box">
            <h3>🔗 Database Connection</h3>
            __DB_STATUS_HTML__
        </div>

        __USERS_FORM_HTML__

        <div class="footer">
            <p>Powered by Flask + Gunicorn + Nginx + MariaDB</p>
            <p>Deployed with Ansible</p>
        </div>
    </div>
</body>
</html>
'''


def get_db_connection():
    import MySQLdb
    return MySQLdb.connect(
        host=app.config.get('DB_HOST', '127.0.0.1'),
        port=app.config.get('DB_PORT', 3306),
        user=app.config.get('DB_USER', 'app_user'),
        passwd=app.config.get('DB_PASSWORD', ''),
        db=app.config.get('DB_NAME', 'app_db'),
        connect_timeout=5
    )


def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB init error: {e}")
        return False


@app.route('/')
def home():
    import platform
    
    db_status = 'disconnected'
    db_version = 'N/A'
    db_error = 'Not configured'
    db_name = app.config.get('DB_NAME', 'N/A')
    users = []
    users_count = 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        db_version = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 10")
        users = cursor.fetchall()
        db_status = 'connected'
        conn.close()
    except Exception as e:
        db_error = str(e)
    
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime = f"{days}d {hours}h {minutes}m"
    except:
        uptime = 'N/A'
    
    app_name = app.config.get('APP_NAME', 'Ansible Lab App')
    
    # Build DB status HTML
    if db_status == 'connected':
        db_html = f'''
            <p class="status ok">✓ Connected to MariaDB</p>
            <p>MariaDB Version: {db_version}</p>
            <p>Database: {db_name}</p>
            <p>Users in DB: {users_count}</p>
        '''
    else:
        db_html = f'<p class="status error">✗ {db_error}</p>'
    
    # Build users form HTML
    if db_status == 'connected':
        users_html = '''
        <div class="user-form">
            <h3>➕ Add User to Database</h3>
            <form method="POST" action="/add_user">
                <input type="text" name="username" placeholder="Username" required>
                <input type="email" name="email" placeholder="Email" required>
                <button type="submit">Add User</button>
            </form>
        </div>
        <div class="users-list">
            <h3>👥 Users from Database</h3>
        '''
        if users:
            for user in users:
                users_html += f'<div class="user-item"><span><strong>{user[1]}</strong> - {user[2]}</span><span>{user[3]}</span></div>'
        else:
            users_html += '<p>No users yet. Add one above!</p>'
        users_html += '</div>'
    else:
        users_html = ''
    
    # Replace placeholders in template
    html = HTML_TEMPLATE.replace('__APP_NAME__', app_name)
    html = html.replace('__HOSTNAME__', socket.gethostname())
    html = html.replace('__PYTHON_VERSION__', sys.version)
    html = html.replace('__FLASK_VERSION__', __import__('flask').__version__)
    html = html.replace('__SERVER_TIME__', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html = html.replace('__OS_INFO__', f"{platform.system()} {platform.release()}")
    html = html.replace('__UPTIME__', uptime)
    html = html.replace('__DB_STATUS_HTML__', db_html)
    html = html.replace('__USERS_FORM_HTML__', users_html)
    
    return html


@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    
    if username and email:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s)",
                (username, email)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error adding user: {e}")
    
    return jsonify({'status': 'ok'}), 201


@app.route('/health')
def health():
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'hostname': socket.gethostname(),
        'python_version': sys.version,
    }
    
    try:
        conn = get_db_connection()
        health_data['database'] = 'connected'
        conn.close()
    except Exception as e:
        health_data['status'] = 'degraded'
        health_data['database'] = f'disconnected: {str(e)}'
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code


@app.route('/api/info')
def api_info():
    return jsonify({
        'hostname': socket.gethostname(),
        'time': datetime.datetime.now().isoformat(),
        'python_version': sys.version,
        'flask_version': __import__('flask').__version__,
        'environment': app.config.get('ENVIRONMENT', 'production')
    })


@app.route('/api/users', methods=['GET'])
def api_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'users': [
                {'id': u[0], 'username': u[1], 'email': u[2], 'created_at': str(u[3])}
                for u in users
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
