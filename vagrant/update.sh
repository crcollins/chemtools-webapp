#!/bin/bash

cd chemtools-webapp
git pull
pip install -r requirements.txt
python manage.py syncdb --noinput
sudo supervisorctl restart chemtools