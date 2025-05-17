#! /bin/bash

echo "Turning it to a Set top box"

if [ ! -d "$HOME/.local/share/applications" ]; then
    echo "Creating directory $HOME/.local/share/applications"
    mkdir -p "$HOME/.local/share/applications"
fi
if [ ! -d "$HOME/.config/autostart" ]; then
    echo "Creating directory $HOME/.config/autostart"
    mkdir -p "$HOME/.config/autostart"
fi

# get the .desktop file and startup.sh
wget -O $HOME/startup.sh https://raw.githubusercontent.com/SNEHASISHROY-125/kivstartv/refs/heads/linux/startup.sh
wget -O $HOME/kivstartv.desktop https://raw.githubusercontent.com/SNEHASISHROY-125/kivstartv/refs/heads/linux/kivstartv.desktop

cp kivstartv.desktop ~/.config/autostart/
chmod +x ~/.config/autostart/kivstartv.desktop

ln -s ~/.local/share/applications/kivstartv.desktop ~/.config/autostart/kivstartv.desktop

chmod +x $HOME/startup.sh

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