#!/usr/bin/env python3
"""
Development environment setup script for Google Maps Scraping project.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "logs",
        "data/raw",
        "data/processed", 
        "data/exports",
        "config",
        "docs/api",
        "docs/user_guide"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")


def setup_python_environment():
    """Setup Python development environment."""
    print("\n🐍 Setting up Python environment...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install development dependencies
    if not run_command(f"{pip_cmd} install pytest pytest-cov black flake8 mypy", "Installing development dependencies"):
        return False
    
    return True


def setup_node_environment():
    """Setup Node.js environment for scrapers."""
    print("\n🟢 Setting up Node.js environment...")
    
    # Check if Node.js is installed
    if not run_command("node --version", "Checking Node.js installation"):
        print("❌ Node.js is not installed. Please install Node.js 16+ and try again.")
        return False
    
    # Install Node.js dependencies
    os.chdir("src/scrapers")
    if not run_command("npm install", "Installing Node.js dependencies"):
        os.chdir("../..")
        return False
    
    os.chdir("../..")
    return True


def create_config_files():
    """Create configuration files if they don't exist."""
    print("\n⚙️ Setting up configuration files...")
    
    # Create local settings file if it doesn't exist
    local_settings = Path("config/settings.local.yaml")
    if not local_settings.exists():
        default_settings = Path("config/settings.yaml")
        if default_settings.exists():
            import shutil
            shutil.copy(default_settings, local_settings)
            print("📄 Created local settings file: config/settings.local.yaml")
        else:
            print("⚠️ No default settings file found")
    
    # Create .env file template
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Environment variables for Google Maps Scraping
# Copy this file to .env.local and fill in your values

# Application settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API Keys (add your actual keys here)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
PROXY_SERVICE_KEY=your_proxy_service_key_here

# Database settings (if using)
DATABASE_URL=sqlite:///data/scraping.db

# Scraping settings
SCRAPING_DELAY=2.0
MAX_RETRIES=3
"""
        env_file.write_text(env_content)
        print("📄 Created .env file template")


def run_tests():
    """Run the test suite to verify setup."""
    print("\n🧪 Running tests to verify setup...")
    
    if run_command("python -m pytest tests/unit/ -v", "Running unit tests"):
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed. This might be expected for initial setup.")


def main():
    """Main setup function."""
    print("🚀 Setting up Google Maps Scraping development environment...")
    
    # Create directories
    create_directories()
    
    # Setup Python environment
    if not setup_python_environment():
        print("❌ Python environment setup failed")
        sys.exit(1)
    
    # Setup Node.js environment
    if not setup_node_environment():
        print("❌ Node.js environment setup failed")
        sys.exit(1)
    
    # Create configuration files
    create_config_files()
    
    # Run tests
    run_tests()
    
    print("\n🎉 Development environment setup completed!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    print("   - Windows: venv\\Scripts\\activate")
    print("   - Unix/Linux/Mac: source venv/bin/activate")
    print("2. Edit config/settings.local.yaml with your settings")
    print("3. Copy .env to .env.local and add your API keys")
    print("4. Run: python main.py --help")
    print("\n📚 For more information, see the README.md file")


if __name__ == "__main__":
    main()
