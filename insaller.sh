#! /bin/bash

echo "Turning it to a Set top box"

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

ln -s ~/.local/share/applications/kivstartv.desktop ~/.config/autostart/kivstartv.desktop

chmod +x $APPDIR/startup.sh

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