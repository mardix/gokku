echo "Bokku installer"

apt-get update
apt-get install -y wget curl cron build-essential certbot git incron \
   libjpeg-dev libxml2-dev libxslt1-dev zlib1g-dev nginx \
   python-certbot-nginx python-dev python-pip python-virtualenv \
   python3-dev python3-pip python3-virtualenv \
   uwsgi uwsgi-plugin-asyncio-python3 uwsgi-plugin-gevent-python \
   uwsgi-plugin-python uwsgi-plugin-python3 uwsgi-plugin-tornado-python \ 
apt-get update

pip install ansible

pip3 install bokku

cd /tmp
wget https://raw.githubusercontent.com/mardix/bokku/master/files/playbook.yml

PYTHONWARNINGS="ignore" ansible-playbook -i localhost, playbook.yml

echo ""
echo "Bokku installation complete!"