#!/usr/bin/env python3
"""
VPN Cloud Project - Main Flask Application
Handles authentication, user management, and WireGuard configuration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import pymysql
import hashlib
import os
import subprocess
import secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'user': os.getenv('DB_USER', 'vpn_api'),
    'password': os.getenv('DB_PASSWORD', 'vpn_api_pass_456'),
    'database': os.getenv('DB_NAME', 'vpn_users'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Create database connection"""
    return pymysql.connect(**DB_CONFIG)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
@require_auth
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        password_hash = hash_password(password)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, username, email, enabled 
                   FROM vpn_users 
                   WHERE username = %s AND password_hash = %s""",
                (username, password_hash)
            )
            user = cursor.fetchone()

            if user and user['enabled']:
                # Update last login
                cursor.execute(
                    """UPDATE vpn_users 
                       SET last_login = NOW() 
                       WHERE id = %s""",
                    (user['id'],)
                )
                conn.commit()

                # Create session
                session['user_id'] = user['id']
                session['username'] = user['username']

                # Log connection
                cursor.execute(
                    """INSERT INTO connection_logs (user_id, action, ip_address) 
                       VALUES (%s, 'login', %s)""",
                    (user['id'], request.remote_addr)
                )
                conn.commit()

                return jsonify({
                    'success': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email']
                    }
                }), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True}), 200

@app.route('/api/config/generate', methods=['POST'])
@require_auth
def generate_config():
    """Generate WireGuard configuration for user"""
    try:
        user_id = session['user_id']
        username = session['username']

        # Generate WireGuard keypair
        private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
        public_key = subprocess.check_output(
            ['wg', 'pubkey'], 
            input=private_key.encode()
        ).decode().strip()

        # Assign IP address (simple allocation)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get next available IP
            cursor.execute(
                """SELECT assigned_ip FROM active_connections 
                   ORDER BY id DESC LIMIT 1"""
            )
            last_conn = cursor.fetchone()

            if last_conn:
                last_ip = last_conn['assigned_ip']
                ip_parts = last_ip.split('.')
                next_ip = f"10.13.13.{int(ip_parts[3]) + 1}"
            else:
                next_ip = "10.13.13.2"

            # Store connection
            cursor.execute(
                """INSERT INTO active_connections 
                   (user_id, public_key, assigned_ip) 
                   VALUES (%s, %s, %s)""",
                (user_id, public_key, next_ip)
            )
            conn.commit()

        # Create WireGuard config
        server_public_key = os.getenv('WIREGUARD_PUBLIC_KEY', 'SERVER_PUBLIC_KEY_HERE')
        server_endpoint = os.getenv('SERVER_ENDPOINT', 'YOUR_SERVER_IP:51820')

        config = f"""[Interface]
    PrivateKey = {private_key}
    Address = {next_ip}/32
    DNS = 1.1.1.1

    [Peer]
    PublicKey = {server_public_key}
    Endpoint = {server_endpoint}
    AllowedIPs = 0.0.0.0/0
    PersistentKeepalive = 25
    """

        return jsonify({
            'success': True,
            'config': config,
            'assigned_ip': next_ip,
            'public_key': public_key
        }), 200

    except Exception as e:
        print(f"Config generation error: {e}")
        return jsonify({'error': 'Failed to generate configuration'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/users/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    try:
        user_id = session['user_id']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, username, email, created_at, last_login 
                   FROM vpn_users WHERE id = %s""",
                (user_id,)
            )
            user = cursor.fetchone()

            if user:
                return jsonify({'success': True, 'user': user}), 200
            else:
                return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to get user'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get VPN server status"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM vpn_users WHERE enabled = 1")
            total_users = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as active FROM active_connections")
            active_connections = cursor.fetchone()['active']

        return jsonify({
            'success': True,
            'status': 'online',
            'total_users': total_users,
            'active_connections': active_connections
        }), 200

    except Exception as e:
        print(f"Status error: {e}")
        return jsonify({'error': 'Failed to get status'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
