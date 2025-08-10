#!/bin/bash

# FarmDepot.ng Voice Assistant Deployment Script
# Run this script to automatically deploy your voice assistant

set -e  # Exit on any error

echo " FarmDepot.ng Voice Assistant Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    print_error "main.py not found. Please run this script from the project directory."
    exit 1
fi

print_step "1. Checking system requirements for multilingual support..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version found "
else
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed."
    exit 1
fi

print_step "2. Setting up virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

print_step "3. Installing Python dependencies..."

# Upgrade pip
pip install --upgrade pip

# Install system dependencies for audio processing
print_status "Installing system audio dependencies..."

if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio ffmpeg
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y portaudio-devel pyaudio ffmpeg
elif command -v brew &> /dev/null; then
    # macOS
    brew install portaudio ffmpeg
else
    print_warning "Could not detect package manager. Please install portaudio and ffmpeg manually."
fi

# Install Python packages with multilingual support
print_status "Installing Python packages with multilingual support..."

pip install --no-cache-dir \
    crewai==0.28.8 \
    crewai-tools==0.1.6 \
    flask==2.3.3 \
    flask-cors==4.0.0 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    gtts==2.4.0 \
    openai-whisper==20231117 \
    speech-recognition==3.10.0 \
    pydub==0.25.1 \
    langchain==0.1.0 \
    langchain-community==0.0.13 \
    pygame==2.5.2 \
    langdetect==1.0.9

# Try to install PyAudio (might fail on some systems)
if pip install pyaudio==0.2.11; then
    print_status "PyAudio installed successfully"
else
    print_warning "PyAudio installation failed. Trying alternative method..."
    
    # Try system package
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pyaudio
    else
        print_warning "Please install PyAudio manually for your system"
    fi
fi

print_step "4. Setting up configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << 'EOL'
# WordPress Configuration
WORDPRESS_URL=https://farmdepot.ng
WORDPRESS_JWT_TOKEN=your_wordpress_jwt_token_here
WORDPRESS_API_KEY=your_wordpress_api_key_here

# OpenRouter AI Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Flask Configuration
FLASK_DEBUG=false
PORT=5000

# Voice Configuration
ENABLE_CONTINUOUS_LISTENING=false
DEFAULT_LANGUAGE=en
VOICE_TIMEOUT=10

# CrewAI Configuration
CREW_MEMORY=true
CREW_VERBOSE=false
EOL
    print_status "Created .env configuration file"
    print_warning "Please edit .env file with your actual API keys and configuration"
else
    print_status ".env file already exists"
fi

print_step "5. Creating directory structure..."

# Create necessary directories
mkdir -p static/voice_responses
mkdir -p templates
mkdir -p logs

print_status "Directory structure created"

print_step "6. Setting up systemd service (for production)..."

# Create systemd service file
if [ "$EUID" -eq 0 ]; then
    cat > /etc/systemd/system/farmdepot-voice.service << EOF
[Unit]
Description=FarmDepot Voice Assistant
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_status "Systemd service created. Use 'sudo systemctl start farmdepot-voice' to start"
else
    print_warning "Not running as root. Systemd service not created."
fi

print_step "7. Testing installation..."

# Test imports
python3 -c "
try:
    import crewai
    import flask
    import speech_recognition
    import gtts
    import whisper
    import pygame
    print(' All critical packages imported successfully')
except ImportError as e:
    print(' Import error:', e)
    exit(1)
" || {
    print_error "Package import test failed"
    exit 1
}

print_step "8. Creating startup script..."

cat > start.sh << 'EOF'
#!/bin/bash
# Startup script for FarmDepot Voice Assistant

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting FarmDepot Voice Assistant..."
python main.py
EOF

chmod +x start.sh
print_status "Created start.sh script"

print_step "9. Creating health check script..."

cat > health_check.py << 'EOF'
#!/usr/bin/env python3
import requests
import sys
import os

def check_health():
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print(" Service is healthy")
            return True
        else:
            print(f" Service returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f" Service is not responding: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
EOF

chmod +x health_check.py
print_status "Created health check script"

print_step "10. Setting up log rotation..."

# Create logrotate configuration
cat > farmdepot-voice-logrotate << EOF
$(pwd)/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $(whoami) $(whoami)
    postrotate
        systemctl reload farmdepot-voice 2>/dev/null || true
    endscript
}
EOF

if [ "$EUID" -eq 0 ]; then
    mv farmdepot-voice-logrotate /etc/logrotate.d/
    print_status "Log rotation configured"
else
    print_warning "Not running as root. Log rotation not configured."
fi

print_step "11. Creating backup script..."

cat > backup.sh << 'EOF'
#!/bin/bash
# Backup script for FarmDepot Voice Assistant

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env *.py templates/ static/

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

echo "Backup created: $BACKUP_DIR/"

# Keep only last 10 backups
ls -t $BACKUP_DIR/*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true
EOF

chmod +x backup.sh
print_status "Created backup script"

echo
echo "==============================================="
print_status "Multilingual deployment completed successfully! "
echo
echo "Languages supported:"
echo "• English - Default language"
echo "• Hausa - Northern Nigeria"
echo "• Igbo - Eastern Nigeria" 
echo "• Yoruba - Western Nigeria"
echo
echo "Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo
echo "2. Test the installation:"
echo "   ./start.sh"
echo
echo "3. For production deployment:"
echo "   sudo systemctl start farmdepot-voice"
echo "   sudo systemctl enable farmdepot-voice"
echo
echo "4. Check service status:"
echo "   ./health_check.py"
echo
echo "5. View logs:"
echo "   tail -f logs/app.log"
echo
echo "6. Create regular backups:"
echo "   ./backup.sh"
echo
print_warning "Don't forget to:"
print_warning "• Configure your WordPress JWT plugin"
print_warning "• Add the WordPress integration code to functions.php"
print_warning "• Test voice functionality in the browser"
print_warning "• Set up SSL certificate for production"
echo
echo "For support, check the documentation or contact your developer."
echo "Happy farming! "