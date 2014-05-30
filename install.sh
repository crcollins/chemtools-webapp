#!/usr/bin/env bash

INSTALL_USER=vagrant
CHEMTOOLS_DIR=/home/$INSTALL_USER/chemtools-webapp
export PIP_DEFAULT_TIMEOUT=600

dependencies() {
    sudo apt-get update
    sudo apt-get install -y git python2.7 python-dev gfortran liblapack-dev\
                            libatlas-dev build-essential libfreetype6-dev\
                            libpng-dev python-cairo python-pip supervisor nginx
    sudo pip install virtualenv
}

install_chemtools() {
    cd $CHEMTOOLS_DIR
    virtualenv .
    . bin/activate
    ln -fs /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

    pip install numpy==1.6.1
    pip install -r requirements.txt
    pip install gunicorn
    python manage.py syncdb --noinput
    sudo tee /etc/cron.d/chemtools <<EOF
PATH=/home/vagrant/chemtools-webapp/bin
0 3 * * * vagrant cd $CHEMTOOLS_DIR && python -u $CHEMTOOLS_DIR/manage.py update_ml >> $CHEMTOOLS_DIR/ml_update.log
EOF
}

setup_nginx() {
    cd $CHEMTOOLS_DIR
    . bin/activate
    sudo sed -e "s/\$INSTALL_USER/$INSTALL_USER/g"      \
             -e "s,\$CHEMTOOLS_DIR,$CHEMTOOLS_DIR,g"    \
             project/nginx_settings.conf                \
             | sudo tee /etc/nginx/sites-available/chemtools
    sudo sed -e "s/\$INSTALL_USER/$INSTALL_USER/g"      \
             -e "s,\$CHEMTOOLS_DIR,$CHEMTOOLS_DIR,g"    \
             project/supervisor_settings.conf           \
             | sudo tee /etc/supervisor/conf.d/chemtools.conf
    sudo ln -fs /etc/nginx/sites-available/chemtools /etc/nginx/sites-enabled/chemtools
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -s reload

    sudo supervisorctl reread
    sudo supervisorctl update
    sudo service nginx restart
}

update() {
    cd $CHEMTOOLS_DIR
    . bin/activate
    git pull
    pip install -r requirements.txt
    python manage.py syncdb --noinput
    sudo supervisorctl restart chemtools
}

remove() {
    sudo rm -rf $CHEMTOOLS_DIR /etc/nginx/sites-available/chemtools \
                /etc/nginx/sites-enabled/chemtools /etc/supervisor/conf.d/chemtools.conf \
                /etc/cron.d/chemtools
    sudo supervisorctl shutdown chemtools
    sudo service nginx restart
}



if [ "$1" == "remove" ];
    then
    echo "Uninstalling"
    remove
else
    dependencies
    install_chemtools
    setup_nginx
fi