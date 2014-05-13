#!/usr/bin/env bash

PROJECT_DIR=/home/vagrant/project
CHEMTOOLS_DIR=$PROJECT_DIR/chemtools-webapp

dependencies() {
    sudo apt-get update
    sudo apt-get install -y git python2.7 python-dev gfortran liblapack-dev\
                            libatlas-dev build-essential libfreetype6-dev\
                            libpng-dev python-cairo python-pip supervisor nginx
    sudo pip install virtualenv
}

install_chemtools() {
    cd $HOME
    # virtualenv
    virtualenv project
    cd $PROJECT_DIR
    . bin/activate
    ln -s /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

    git clone https://github.com/crcollins/chemtools-webapp.git
    cd $CHEMTOOLS_DIR
    pip install numpy==1.6.1
    pip install -r requirements.txt
    python manage.py syncdb --noinput

    # deploy
    pip install gunicorn

    sudo sh -c 'sed project/nginx.conf -e "s/chris/vagrant/g" > /etc/nginx/nginx.conf'
    sudo nginx -s reload
    sudo sh -c 'sed project/chemtools.conf -e "s/chris/vagrant/g" > /etc/supervisor/conf.d/chemtools.conf'

    sudo supervisorctl reread
    sudo supervisorctl update
    sudo service nginx stop
    sudo service nginx start
}

update() {
    cd $CHEMTOOLS_DIR
    git pull
    pip install -r requirements.txt
    python manage.py syncdb --noinput
    sudo supervisorctl restart chemtools
}

dependencies
install_chemtools
