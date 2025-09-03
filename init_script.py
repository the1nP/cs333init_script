#!/usr/bin/env python3

import os
import subprocess
import logging
import sys

# =========================
# Configurable variables (override with environment variables if needed)
# =========================
PROJECT_NAME = os.environ.get("PROJECT_NAME", "cs333_FinalProject")
BASE_DIR = os.environ.get("PROJECT_BASE_DIR", "/srv")
PROJECT_DIR = os.path.join(BASE_DIR, PROJECT_NAME)

VENV_DIR = os.path.join(PROJECT_DIR, "venv")
VENV_PIP = os.path.join(VENV_DIR, "bin", "pip")
VENV_ACTIVATE = os.path.join(VENV_DIR, "bin", "activate")
GUNICORN_BIN = os.path.join(VENV_DIR, "bin", "gunicorn")

# Domain and app port can be set once here
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "2tooltrack.m3chok.com")
APP_PORT = int(os.environ.get("APP_PORT", "8000"))

# Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/init_tooltrack.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_virtual_environment():
    """Create and activate virtual environment, then install requirements."""
    try:
        # Navigate to project directory
        log_message(f"Changing to project directory: {PROJECT_DIR}")
        os.makedirs(PROJECT_DIR, exist_ok=True)
        os.chdir(PROJECT_DIR)
        
        # Create virtual environment
        log_message("Creating Python virtual environment")
        subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)
        
        # Install requirements if requirements.txt exists
        if os.path.exists('requirements.txt'):
            log_message("Installing project dependencies from requirements.txt")
            subprocess.run([VENV_PIP, 'install', '-r', 'requirements.txt'], check=True)
            log_message("Project dependencies installed successfully")
        else:
            log_message("No requirements.txt found, skipping dependency installation", logging.WARNING)
        
        log_message("Virtual environment setup complete")
        log_message(f"To activate the environment, run: source {VENV_ACTIVATE}")
        
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to setup virtual environment: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while setting up virtual environment: {str(e)}", logging.ERROR)
        return False

def log_message(message, level=logging.INFO):
    """Log message to file and console"""
    if level == logging.INFO:
        logging.info(message)
    elif level == logging.ERROR:
        logging.error(message)
    elif level == logging.WARNING:
        logging.warning(message)

def install_prerequisites():
    """Install required system packages"""
    try:
        log_message("Updating package lists")
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        
        log_message("Installing Python dependencies (python3-venv, python3-pip)")
        subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-venv', 'python3-pip'], check=True)
        
        log_message("Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to install Python dependencies: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while installing Python dependencies: {str(e)}", logging.ERROR)
        return False

def clone_repository():
    """Clone the application repository into BASE_DIR directory."""
    try:
        # Create the base directory if it doesn't exist
        if not os.path.exists(BASE_DIR):
            log_message(f"Creating base directory {BASE_DIR}")
            subprocess.run(['sudo', 'mkdir', '-p', BASE_DIR], check=True)
            
        # Set proper permissions
        log_message(f"Setting permissions for base directory {BASE_DIR}")
        subprocess.run(['sudo', 'chown', f'{os.getenv("USER")}:{os.getenv("USER")}', BASE_DIR], check=True)
        
        # Clone repository (replace with your actual repository URL)
        repo_url = "https://github.com/pakin6509681182/cs333_FinalProject.git"
        target_dir = PROJECT_DIR
        if os.path.exists(target_dir):
            log_message(f"Target directory {target_dir} already exists. Removing it.")
            subprocess.run(['sudo', 'rm', '-rf', target_dir], check=True)
        else:
            log_message(f"Target directory {target_dir} does not exist. Proceeding with clone.")
        
        log_message(f"Cloning repository from {repo_url} to {target_dir}")
        subprocess.run(['git', 'clone', repo_url, target_dir], check=True)
        
        log_message("Repository cloned successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to clone repository: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while cloning repository: {str(e)}", logging.ERROR)
        return False

def setup_apache_reverse_proxy():
    """Configure Apache2 as a reverse proxy for the Tooltrack application"""
    try:
        log_message("Installing Apache2 server")
        subprocess.run(['sudo', 'apt', 'install', '-y', 'apache2'], check=True)
        
        log_message("Stopping Tooltrack service temporarily")
        subprocess.run(['sudo', 'systemctl', 'stop', 'tooltrack'], check=True)
        
        # Create virtual host configuration using DOMAIN_NAME and APP_PORT
        vhost_content = f"""<VirtualHost *:80>
        ServerName {DOMAIN_NAME}
        ServerAlias www.{DOMAIN_NAME}

        ProxyPass / http://127.0.0.1:{APP_PORT}/
        ProxyPassReverse / http://127.0.0.1:{APP_PORT}/

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
"""
        apache_conf_dir = "/etc/apache2/sites-available"
        vhost_file = f"{apache_conf_dir}/{DOMAIN_NAME}.conf"
        
        log_message(f"Configuring Apache2 virtual host for {DOMAIN_NAME}")
        
        # First remove the default SSL configuration if it exists
        subprocess.run(['sudo', 'rm', '-f', f"{apache_conf_dir}/default-ssl.conf"], check=True)
        
        # Rename the default configuration
        if os.path.exists(f"{apache_conf_dir}/000-default.conf"):
            log_message("Removing default Apache2 configuration")
            subprocess.run(['sudo', 'mv', f"{apache_conf_dir}/000-default.conf", vhost_file], check=True)
        
        # Write our new configuration - use DOMAIN_NAME for the temp file name too
        with open(f"/tmp/{DOMAIN_NAME}.conf", "w") as temp_file:
            temp_file.write(vhost_content)
        subprocess.run(['sudo', 'cp', f'/tmp/{DOMAIN_NAME}.conf', vhost_file], check=True)
        
        log_message("Enabling required Apache2 modules")
        subprocess.run(['sudo', 'a2enmod', 'proxy', 'proxy_http'], check=True)
        
        log_message("Disabling default site and enabling Tooltrack site")
        try:
            subprocess.run(['sudo', 'a2dissite', '000-default.conf'], check=True, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            log_message("Default site 000-default.conf does not exist, continuing anyway", logging.WARNING)
        subprocess.run(['sudo', 'a2ensite', f'{DOMAIN_NAME}.conf'], check=True)
        
        log_message("Reloading Apache2 configuration")
        subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
        
        log_message("Restarting Tooltrack service")
        subprocess.run(['sudo', 'systemctl', 'start', 'tooltrack'], check=True)
        
        log_message("Apache2 reverse proxy setup complete")
        log_message(f"Tooltrack is now accessible at http://{DOMAIN_NAME}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to set up Apache2 reverse proxy: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while setting up Apache2 reverse proxy: {str(e)}", logging.ERROR)
        return False

def setup_background_service():
    """Configure and start the Tooltrack web server as a background service"""
    try:
        service_file_path = "/etc/systemd/system/tooltrack.service"
        service_content = f"""[Unit]
Description=Tooltrack Web Server

[Service]
ExecStart={GUNICORN_BIN} app:app -w 4 -b 127.0.0.1:{APP_PORT}
WorkingDirectory={PROJECT_DIR}
Restart=on-failure
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
"""
        
        log_message("Creating systemd service file for Tooltrack")
        with open("/tmp/tooltrack.service", "w") as temp_file:
            temp_file.write(service_content)
        
        subprocess.run(['sudo', 'cp', '/tmp/tooltrack.service', service_file_path], check=True)
        
        log_message("Reloading systemd daemon")
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        log_message("Starting Tooltrack service")
        subprocess.run(['sudo', 'systemctl', 'start', 'tooltrack'], check=True)
        
        log_message("Enabling Tooltrack service to start on boot")
        subprocess.run(['sudo', 'systemctl', 'enable', 'tooltrack'], check=True)
        
        log_message("Tooltrack service successfully set up and started")
        log_message("Service status: sudo systemctl status tooltrack")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to set up Tooltrack service: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while setting up Tooltrack service: {str(e)}", logging.ERROR)
        return False

def setup_ssl_certificates():
    """Install Certbot and configure SSL certificates for the domain"""
    try:
        log_message("Installing Certbot via snap")
        subprocess.run(['sudo', 'snap', 'install', '--classic', 'certbot'], check=True)
        
        log_message("Creating symlink for certbot")
        subprocess.run(['sudo', 'ln', '-sf', '/snap/bin/certbot', '/usr/bin/certbot'], check=True)
        
        log_message("Obtaining SSL certificates with Certbot")
        
        # Create expect script to handle interactive prompts
        expect_script = """#!/usr/bin/expect
set timeout 300
spawn sudo certbot --apache
expect "Enter email address"
send "the1name@outlook.com\\r"
expect "the Terms of Service"
send "Y\\r"
expect "share your email"
send "N\\r"
expect "Select the appropriate number"
send "\\r"
expect eof
"""
        with open("/tmp/certbot_expect.exp", "w") as f:
            f.write(expect_script)
        
        subprocess.run(['chmod', '+x', '/tmp/certbot_expect.exp'], check=True)
        subprocess.run(['sudo', 'apt', 'install', '-y', 'expect'], check=True)
        
        log_message("Running Certbot to obtain SSL certificates")
        subprocess.run(['/tmp/certbot_expect.exp'], check=True, stderr=subprocess.DEVNULL)
        
        log_message("SSL certificates successfully obtained and configured")
        log_message(f"Website is now accessible via HTTPS: https://{DOMAIN_NAME}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to set up SSL certificates: {str(e)}", logging.ERROR)
        return False
    except Exception as e:
        log_message(f"Unexpected error while setting up SSL certificates: {str(e)}", logging.ERROR)
        return False

if __name__ == "__main__":
    print("=" * 60)
    log_message("Starting initialization process for the web application")
    print("=" * 60)
    
    # Install required system packages
    prereq_success = install_prerequisites()
    if not prereq_success:
        log_message("Failed to install prerequisites. Exiting.", logging.ERROR)
        sys.exit(1)
        
    # Clone the repository
    clone_success = clone_repository()
    if not clone_success:
        log_message("Failed to clone repository. Exiting.", logging.ERROR)
        sys.exit(1)
    
    # Set up the virtual environment and install requirements
    venv_success = setup_virtual_environment()
    if not venv_success:
        log_message("Failed to set up virtual environment. Exiting.", logging.ERROR)
        sys.exit(1)
    
    # Configure and start the background service
    service_success = setup_background_service()
    if not service_success:
        log_message("Failed to set up background service. Exiting.", logging.ERROR)
        sys.exit(1)
    
    # Set up Apache2 as a reverse proxy
    apache_success = setup_apache_reverse_proxy()
    if not apache_success:
        log_message("Failed to set up Apache2 reverse proxy. Exiting.", logging.ERROR)
        sys.exit(1)
    
    log_message("Application setup completed successfully")
    log_message(f"Tooltrack web server is now running and accessible at http://{DOMAIN_NAME}")

    # Set up SSL certificates with Certbot
    ssl_success = setup_ssl_certificates()
    if not ssl_success:
        log_message("Failed to set up SSL certificates. Exiting.", logging.ERROR)
        sys.exit(1)
    
    log_message("Application setup completed successfully")
    log_message(f"Tooltrack web server is now running and accessible at https://{DOMAIN_NAME}")
