#!/bin/bash

echo "Updating package lists..."
sudo apt-get update

echo "Installing system dependencies..."
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-dev
sudo apt-get install -y vlc
sudo apt-get install -y pigpio

echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python packages..."
pip3 install flask
pip3 install flask-cors
pip3 install gpiozero
pip3 install python-vlc
pip3 install pigpio
pip3 install toml

echo "Starting GPIO daemon..."
sudo pigpiod

echo "Installation complete!"
echo "To activate the virtual environment in the future, run: source .venv/bin/activate"
echo "Remember to run 'sudo pigpiod' if you restart your Raspberry Pi" 