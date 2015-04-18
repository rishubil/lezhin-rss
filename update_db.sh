#!/bin/bash
cd /usr/share/nginx/www/lezhin-rss
. venv/bin/activate
python update.py
deactivate
