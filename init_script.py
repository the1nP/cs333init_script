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
    
    log_message("Application setup completed successfully")