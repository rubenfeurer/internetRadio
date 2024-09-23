#!/bin/bash

sleep 5

lxterminal -e bash -c "
	cd /home/rubenfeurer/internetRadio
	source /home/rubenfeurer/internetRadio/.venv/bin/activate
	sudo pigpiod
	python /home/rubenfeurer/internetRadio/main.py"