echo "Bokku installer"

apt-get update
apt-get install -y wget curl cron build-essential certbot git incron \
    libjpeg-dev libxml2-dev libxslt1-dev zlib1g-dev nginx \
    python-certbot-nginx python-dev python-pip python-virtualenv \
    python3-dev python3-pip python3-virtualenv \
    uwsgi uwsgi-plugin-asyncio-python3 uwsgi-plugin-gevent-python \
    uwsgi-plugin-python uwsgi-plugin-python3 uwsgi-plugin-tornado-python
apt-get update

adduser --disabled-password --gecos 'PaaS access' --ingroup www-data bokku

cd /tmp
wget https://raw.githubusercontent.com/mardix/bokku/master/files/incron.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/nginx.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/uwsgi-bokku.service

cp /tmp/nginx.conf /etc/nginx/sites-available/default
cp /tmp/incron.conf /etc/incron.d/bokku
cp /tmp/uwsgi-bokku.service /etc/systemd/system/
ln -s `which uwsgi` /usr/local/bin/uwsgi-bokku

systemctl restart incron
systemctl restart nginx
systemctl disable uwsgi
systemctl enable uwsgi-bokku

pip3 install bokku --upgrade
bokku init

# SSH
cp ~/.ssh/authorized_keys /tmp/authorized_keys
bokku set-ssh /tmp/authorized_keys

systemctl start uwsgi-bokku

# su - bokku
# mkdir ~/.ssh
# chmod 700 ~/.ssh
# Now import your SSH key using setup:ssh

echo ""
echo "Bokku installation complete!"
echo "Bokku installer"

apt-get update
apt-get install -y wget curl cron build-essential certbot git incron \
   libjpeg-dev libxml2-dev libxslt1-dev zlib1g-dev nginx \
   python-certbot-nginx python-dev python-pip python-virtualenv \
   python3-dev python3-pip python3-virtualenv \
   uwsgi uwsgi-plugin-asyncio-python3 uwsgi-plugin-gevent-python \
   uwsgi-plugin-python uwsgi-plugin-python3 uwsgi-plugin-tornado-python
apt-get update

cd /tmp
wget https://raw.githubusercontent.com/mardix/bokku/master/files/incron.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/nginx.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/uwsgi-bokku.service

cp /tmp/nginx.conf /etc/nginx/sites-available/default
cp /tmp/incron.conf /etc/incron.d/bokku
cp /tmp/uwsgi-bokku.service /etc/systemd/system/
ln -s `which uwsgi` /usr/local/bin/uwsgi-bokku

systemctl restart incron
systemctl restart nginx
systemctl disable uwsgi
systemctl enable uwsgi-bokku
systemctl start uwsgi-bokku

pip3 install bokku --upgrade
bokku init

#
ssh-keygen -f $HOME/.ssh/id_rsa -t rsa -N ''
cp  ~/.ssh/id_rsa.pub /tmp/id_rsa.pub


#>>>
adduser --disabled-password --gecos 'PaaS access' --ingroup www-data bokku
su - bokku
mkdir ~/.ssh
chmod 700 ~/.ssh
bokku set-ssh /tmp/id_rsa.pub
exit
#<<<

echo ""
echo "Bokku installation complete!"