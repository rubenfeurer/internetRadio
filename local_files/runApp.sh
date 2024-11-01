#!/bin/bash

sleep 5

lxterminal -e bash -c "
	cd /home/radio/internetRadio
	source /home/radio/internetRadio/.venv/bin/activate
	sudo pigpiod
	python /home/radio/internetRadio/main.py"
