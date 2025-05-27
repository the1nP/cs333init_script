#!/usr/bin/env python3

import os
import subprocess
import logging
import sys

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
        target_dir = "/srv/cs333_FinalProject"
        
        # Navigate to project directory
        log_message(f"Changing to project directory: {target_dir}")
        os.chdir(target_dir)
        
        # Create virtual environment
        log_message("Creating Python virtual environment")
        subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)
        
        # Install requirements if requirements.txt exists
        if os.path.exists('requirements.txt'):
            log_message("Installing project dependencies from requirements.txt")
            # Use the venv's pip directly rather than activating the environment
            subprocess.run(['./venv/bin/pip', 'install', '-r', 'requirements.txt'], check=True)
            log_message("Project dependencies installed successfully")
        else:
            log_message("No requirements.txt found, skipping dependency installation", logging.WARNING)
        
        # Create activation instructions
        log_message("Virtual environment setup complete")
        log_message("To activate the environment, run: source /srv/cs333_FinalProject/venv/bin/activate")
        
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
        
        log_message("Installing Python dependencies (python3.12-venv, python3-pip)")
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
    """Clone the application repository into /srv directory."""
    try:
        # Create the directory if it doesn't exist
        if not os.path.exists('/srv'):
            log_message("Creating /srv directory")
            subprocess.run(['sudo', 'mkdir', '-p', '/srv'], check=True)
            
        # Set proper permissions
        log_message("Setting permissions for /srv directory")
        subprocess.run(['sudo', 'chown', f'{os.getenv("USER")}:{os.getenv("USER")}', '/srv'], check=True)
        
        # Clone repository (replace with your actual repository URL)
        repo_url = "https://github.com/pakin6509681182/cs333_FinalProject.git"
        target_dir = "/srv/cs333_FinalProject"
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
        # Define domain name at the beginning of the function
        domain_name = "2tooltrack.m3chok.com"
        app_port = 8000
        
        log_message("Installing Apache2 server")
        subprocess.run(['sudo', 'apt', 'install', '-y', 'apache2'], check=True)
        
        log_message("Stopping Tooltrack service temporarily")
        subprocess.run(['sudo', 'systemctl', 'stop', 'tooltrack'], check=True)
        
        # Create virtual host configuration using the domain_name variable
        vhost_content = f"""<VirtualHost *:80>
        ServerName {domain_name}
        ServerAlias www.{domain_name}

        ProxyPass / http://127.0.0.1:{app_port}/
        ProxyPassReverse / http://127.0.0.1:{app_port}/

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
"""
        apache_conf_dir = "/etc/apache2/sites-available"
        vhost_file = f"{apache_conf_dir}/{domain_name}.conf"
        
        log_message(f"Configuring Apache2 virtual host for {domain_name}")
        
        # First remove the default SSL configuration if it exists
        subprocess.run(['sudo', 'rm', '-f', f"{apache_conf_dir}/default-ssl.conf"], check=True)
        
        # Rename the default configuration
        if os.path.exists(f"{apache_conf_dir}/000-default.conf"):
            log_message("Removing default Apache2 configuration")
            subprocess.run(['sudo', 'mv', f"{apache_conf_dir}/000-default.conf", 
                           vhost_file], check=True)
        
        # Write our new configuration - use domain_name for the temp file name too
        with open(f"/tmp/{domain_name}.conf", "w") as temp_file:
            temp_file.write(vhost_content)
            
        subprocess.run(['sudo', 'cp', f'/tmp/{domain_name}.conf', vhost_file], check=True)
        
        log_message("Enabling required Apache2 modules")
        subprocess.run(['sudo', 'a2enmod', 'proxy', 'proxy_http'], check=True)
        
        log_message("Disabling default site and enabling Tooltrack site")
        subprocess.run(['sudo', 'a2dissite', '000-default.conf'], check=True, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'a2ensite', f'{domain_name}.conf'], check=True)
        
        log_message("Reloading Apache2 configuration")
        subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'], check=True)
        
        log_message("Restarting Tooltrack service")
        subprocess.run(['sudo', 'systemctl', 'start', 'tooltrack'], check=True)
        
        log_message("Apache2 reverse proxy setup complete")
        log_message(f"Tooltrack is now accessible at http://{domain_name}")
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
        service_content = """[Unit]
Description=Tooltrack Web Server

[Service]
ExecStart=/srv/cs333_FinalProject/venv/bin/gunicorn app:app -w 4 -b 127.0.0.1:8000
WorkingDirectory=/srv/cs333_FinalProject/
Restart=on-failure
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
"""
        
        log_message("Creating systemd service file for Tooltrack")
        # Write service content to a temporary file
        with open("/tmp/tooltrack.service", "w") as temp_file:
            temp_file.write(service_content)
        
        # Copy temporary file to systemd directory
        subprocess.run(['sudo', 'cp', '/tmp/tooltrack.service', service_file_path], check=True)
        
        log_message("Reloading systemd daemon")
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        log_message("Starting Tooltrack service")
        subprocess.run(['sudo', 'systemctl', 'start', 'tooltrack'], check=True)
        
        # Enable service to start on boot
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
    # Use the same domain name as in the setup_apache_reverse_proxy function
    domain_name = "2tooltrack.m3chok.com"  # This should match the one in setup_apache_reverse_proxy
    log_message("Application setup completed successfully")
    log_message(f"Tooltrack web server is now running and accessible at http://{domain_name}")