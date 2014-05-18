#!/usr/bin/env bash

INSTALL_USER=vagrant
PROJECT_DIR=/home/$INSTALL_USER/project
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
    virtualenv project
    cd $PROJECT_DIR
    . bin/activate
    ln -s /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

    git clone https://github.com/crcollins/chemtools-webapp.git
    cd $CHEMTOOLS_DIR
    pip install numpy==1.6.1
    pip install -r requirements.txt
    python manage.py syncdb --noinput
    python manage.py load_data base_data.csv
    pip install gunicorn
}

update() {
    cd $PROJECT_DIR
    . bin/activate

    cd $CHEMTOOLS_DIR
    git pull
    pip install -r requirements.txt
    python manage.py syncdb --noinput
    sudo supervisorctl restart chemtools
}

dependencies
install_chemtools

sudo tee /etc/supervisor/conf.d/chemtools.conf <<EOF
[program:chemtools]
command=$PROJECT_DIR/bin/gunicorn project.wsgi:application
directory=$CHEMTOOLS_DIR
user=$INSTALL_USER
autostart=true
autorestart=true
redirect_stderr=true
EOF

sudo tee /etc/nginx/sites-available/chemtools <<EOF
server {
    listen 80 default;
    client_max_body_size 4G;
    server_name gauss.crcollins.com;
    keepalive_timeout 5;

    root $CHEMTOOLS_DIR/project;
    location /static {
        autoindex on;
        alias $CHEMTOOLS_DIR/project/static;
    }

    location / {
      proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
      proxy_set_header Host \\\$http_host;
      proxy_redirect off;
      proxy_pass http://127.0.0.1:8000/;

    }

    error_page 500 502 503 504 /500.html;
    location = /500.html {
      root $CHEMTOOLS_DIR/project/static;
    }
}
EOF


sudo ln -s /etc/nginx/sites-available/chemtools /etc/nginx/sites-enabled/chemtools
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -s reload

sudo supervisorctl reread
sudo supervisorctl update
sudo service nginx restart