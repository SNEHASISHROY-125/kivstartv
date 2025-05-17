#!/bin/bash

# Set the repo URL and app folder name
REPO_URL="https://github.com/SNEHASISHROY-125/kivstartv.git"
APP_DIR="/opt/kivstartv"

# system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip git
sudo apt install python3-venv

# Check if the directory exists, if not create it
if [ ! -d "$APP_DIR" ]; then
    echo "Creating directory $APP_DIR"
    sudo mkdir -p "$APP_DIR"
    # Clone the repository
    echo "Cloning repository..."
    git clone "$REPO_URL"
fi

cd "kivstartv" || exit

# switch to linux branch
git checkout linux
git pull

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
	echo "Creating virtual environment..."
	python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi

# Launch the app
echo "Launching KivstarTV..."
python3 main.py
