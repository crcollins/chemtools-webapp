#!/usr/bin/env bash

cd ~/project/
. bin/activate

git clone https://github.com/crcollins/chemtools-webapp.git
cd chemtools-webapp
pip install numpy==1.6.1
pip install -r requirements.txt
python manage.py syncdb --noinput

