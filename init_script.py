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

if __name__ == "__main__":
    print("=" * 60)
    log_message("Starting initialization process for the web application")
    print("=" * 60)
    
    # Install required system packages
    prereq_success = install_prerequisites()
    if not prereq_success:
        log_message("Failed to install prerequisites. Exiting.", logging.ERROR)
        sys.exit(1)
        
    success = clone_repository()
    
    if success:
        log_message("Repository setup completed successfully")
    else:
        log_message("Repository setup failed, check logs for details", logging.ERROR)