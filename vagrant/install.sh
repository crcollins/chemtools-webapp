#!/usr/bin/env bash

# dependencies
sudo apt-get update
sudo apt-get install -y git python2.7 python-dev gfortran liblapack-dev libatlas-dev build-essential libfreetype6-dev libpng-dev python-cairo python-pip
sudo pip install virtualenv

# virtualenv
virtualenv project
cd project/
. bin/activate
ln -s /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

# chemtools.sh
# cd ~/project/
# . bin/activate

git clone https://github.com/crcollins/chemtools-webapp.git
cd chemtools-webapp
pip install numpy==1.6.1
pip install -r requirements.txt
python manage.py syncdb --noinput

# deploy.sh
# cd ~/project/
# . bin/activate

sudo apt-get install -y supervisor nginx
pip install gunicorn

sudo sh -c 'sed project/nginx.conf -e "s/chris/vagrant/g" > /etc/nginx/nginx.conf'
sudo nginx -s reload
sudo sh -c 'sed project/chemtools.conf -e "s/chris/vagrant/g" > /etc/supervisor/conf.d/chemtools.conf'


sudo supervisorctl reread
sudo supervisorctl update
sudo service nginx stop
sudo service nginx start
