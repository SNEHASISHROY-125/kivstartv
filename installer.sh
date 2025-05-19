#! /bin/bash

echo "Turning it to a Set top box"

HOME=$(eval echo "~$SUDO_USER")
APPDIR=/opt/kivstartv

if [ ! -d "$APPDIR" ]; then
    echo "Creating directory $APPDIR"
    sudo mkdir -p $APPDIR
fi

if [ ! -d "$HOME/.local/share/applications" ]; then
    echo "Creating directory $HOME/.local/share/applications"
    mkdir -p "$HOME/.local/share/applications"
fi
if [ ! -d "$HOME/.config/autostart" ]; then
    echo "Creating directory $HOME/.config/autostart"
    mkdir -p "$HOME/.config/autostart"
fi

# get the .desktop file and startup.sh
wget -O $APPDIR/startup.sh https://raw.githubusercontent.com/SNEHASISHROY-125/kivstartv/refs/heads/linux/startup.sh
wget -O $APPDIR/kivstartv.desktop https://raw.githubusercontent.com/SNEHASISHROY-125/kivstartv/refs/heads/linux/kivstartv.desktop

cp $APPDIR/kivstartv.desktop ~/.config/autostart/kivstartv.desktop
chmod +x ~/.config/autostart/kivstartv.desktop

cp $APPDIR/kivstartv.desktop ~/.local/share/applications/kivstartv.desktop
ln -sf ~/.local/share/applications/kivstartv.desktop ~/.config/autostart/kivstartv.desktop

chmod +x $APPDIR/startup.sh

# Set the repo URL and app folder name
REPO_URL="https://github.com/SNEHASISHROY-125/kivstartv.git"
APP_DIR="/opt/kivstartv"

# system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip git
sudo apt install python3-venv

# Check if the directory exists, if not create it
# if [ ! -d "$APP_DIR" ]; then
#     echo "Creating directory $APP_DIR"
#     sudo mkdir -p "$APP_DIR"
#     cd "$APP_DIR" || exit
#     # Clone the repository
#     echo "Cloning repository..."
#     git clone "$REPO_URL"
# fi

cd "$APP_DIR" || exit
# Clone the repository
echo "Cloning repository..."
git clone "$REPO_URL"
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
echo "Activating virtual environment..."
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

# ask user wheather to reboot
read -p "Do you want to reboot now? (y/n): " answer
while [[ ! "$answer" =~ ^[yYnN]$ ]]; do
    echo "Invalid input. Please enter 'y' or 'n'."
    read -p "Do you want to reboot now? (y/n): " answer
done

if [ "$answer" == "y" ]; then
    echo "Rebooting..."
    sudo reboot
else
    echo "Reboot canceled."
fi