-- VPN Users Database Initialization
-- Created: 2025-10-18

CREATE DATABASE IF NOT EXISTS vpn_users;
USE vpn_users;

-- Users table with authentication
CREATE TABLE IF NOT EXISTS vpn_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    email VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Active VPN connections tracking
CREATE TABLE IF NOT EXISTS active_connections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    public_key VARCHAR(128),
    assigned_ip VARCHAR(15) NOT NULL,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_handshake TIMESTAMP NULL,
    bytes_sent BIGINT DEFAULT 0,
    bytes_received BIGINT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES vpn_users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Connection logs
CREATE TABLE IF NOT EXISTS connection_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(32) NOT NULL,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES vpn_users(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default test users (passwords are SHA-256 hashed)
-- student1:password123
-- demo:demo123
-- testuser:testpass123
INSERT INTO vpn_users (username, password_hash, email, enabled) VALUES
('student1', SHA2('password123', 256), 'student1@example.com', TRUE),
('demo', SHA2('demo123', 256), 'demo@example.com', TRUE),
('testuser', SHA2('testpass123', 256), 'test@example.com', TRUE),
('admin', SHA2('admin@vpn2025', 256), 'admin@example.com', TRUE)
ON DUPLICATE KEY UPDATE username=username;

-- Create admin user for management
CREATE USER IF NOT EXISTS 'vpn_admin'@'%' IDENTIFIED BY 'admin_secure_789';
GRANT ALL PRIVILEGES ON vpn_users.* TO 'vpn_admin'@'%';
FLUSH PRIVILEGES;

SELECT 'Database initialized successfully' AS status;
