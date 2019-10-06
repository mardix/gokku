
echo "Gokku 0.2.0 installer"

apt-get update
apt-get install -y wget curl cron build-essential certbot git incron \
   libjpeg-dev libxml2-dev libxslt1-dev zlib1g-dev nginx \
   python-certbot-nginx python-dev python-pip python-virtualenv \
   python3-dev python3-pip python3-click python3-virtualenv \
   uwsgi uwsgi-plugin-asyncio-python3 uwsgi-plugin-gevent-python \
   uwsgi-plugin-python uwsgi-plugin-python3 uwsgi-plugin-tornado-python\
   php-fpm nodejs npm
apt-get update

PAAS_USERNAME=gokku

# Create user
sudo adduser --disabled-password --gecos 'PaaS access' --ingroup www-data $PAAS_USERNAME

# copy your public key to /tmp (assuming it's the first entry in authorized_keys)
head -1 ~/.ssh/authorized_keys > /tmp/pubkey
# install gokku and have it set up SSH keys and default files
sudo su - $PAAS_USERNAME -c "wget https://raw.githubusercontent.com/mardix/gokku/master/gokku.py && python3 ~/gokku.py init && python3 ~/gokku.py set-ssh /tmp/pubkey"
rm /tmp/pubkey


sudo ln /home/$PAAS_USERNAME/.gokku/uwsgi/uwsgi.ini /etc/uwsgi/apps-enabled/gokku.ini
sudo systemctl restart uwsgi

cd /tmp
wget https://raw.githubusercontent.com/mardix/gokku/master/files/incron.conf
wget https://raw.githubusercontent.com/mardix/gokku/master/files/nginx.conf
cp /tmp/nginx.conf /etc/nginx/sites-available/default
cp /tmp/incron.conf /etc/incron.d/gokku

echo ""
echo "Gokku installation complete!"