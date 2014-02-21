#!/usr/bin/env bash

cd ~/project/
. bin/activate

sudo apt-get install -y supervisor nginx
pip install gunicorn

sudo sh -c 'sed chemtools-webapp/project/nginx.conf -e "s/chris/vagrant/g" > /etc/nginx/nginx.conf'
sudo nginx -s reload
sudo sh -c 'sed chemtools-webapp/project/chemtools.conf -e "s/chris/vagrant/g" > /etc/supervisor/conf.d/chemtools.conf'


sudo supervisorctl reread
sudo supervisorctl update
sudo service nginx stop
sudo service nginx start
