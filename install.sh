echo "Welcome to Koka installer"

sudo apt-get update
sudo apt-get -y dist-upgrade
sudo apt-get -y autoremove
apt-get -y install  wget cron bc git build-essential libpcre3-dev zlib1g-dev python python3 python3-pip python3-dev python-pip python-setuptools python3-setuptools nginx incron acl
sudo adduser --disabled-password --gecos 'PaaS access' --ingroup www-data koka

# move to /tmp and grab our distribution files
cd /tmp
wget https://raw.githubusercontent.com/mardix/koka/master/files/incron.dist
wget https://raw.githubusercontent.com/mardix/koka/master/files/nginx.default.dist
wget https://raw.githubusercontent.com/koka/koka/master/files/uwsgi-koka.service

echo "Set up nginx to pick up our config files"
sudo cp /tmp/nginx.default.conf /etc/nginx/sites-available/default

echo "Set up incron to reload nginx upon config changes"
sudo cp /tmp/incron.conf /etc/incron.d/koka
sudo systemctl restart incron
sudo systemctl restart nginx
sudo cp /tmp/uwsgi-koka.service /etc/systemd/system/

refer to our executable using a link, in case there are more versions installed
sudo ln -s `which uwsgi` /usr/local/bin/uwsgi-koka
# disable the standard uwsgi startup script
sudo systemctl disable uwsgi
sudo systemctl enable uwsgi-koka
sudo su - koka
mkdir ~/.ssh
chmod 700 ~/.ssh
# now copy the koka script to this user account
cp /tmp/koka.py ~/koka.py
python3 koka.py setup
# Now import your SSH key using setup:ssh

sudo systemctl start uwsgi-koka