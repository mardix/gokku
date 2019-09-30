echo "Bokku installer"

apt-get update
apt-get -y dist-upgrade
apt-get -y autoremove
apt-get -y install  wget curl cron bc git build-essential libpcre3-dev zlib1g-dev python python3 python3-pip python3-dev python-pip python-setuptools python3-setuptools nginx incron acl
apt-get update
pip install uwsgi

adduser --disabled-password --gecos 'PaaS access' --ingroup www-data bokku

# move to /tmp and grab our distribution files
cd /tmp
wget https://raw.githubusercontent.com/mardix/bokku/master/files/incron.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/nginx.conf
wget https://raw.githubusercontent.com/mardix/bokku/master/files/uwsgi-bokku.service

# Set up nginx to pick up our config files
cp /tmp/nginx.conf /etc/nginx/sites-available/default

# Set up incron to reload nginx upon config changes
cp /tmp/incron.conf /etc/incron.d/bokku
systemctl restart incron
systemctl restart nginx
cp /tmp/uwsgi-bokku.service /etc/systemd/system/

#refer to our executable using a link, in case there are more versions installed
ln -s `which uwsgi` /usr/local/bin/uwsgi-bokku
# disable the standard uwsgi startup script
systemctl disable uwsgi
systemctl enable uwsgi-bokku
su - bokku
mkdir ~/.ssh
chmod 700 ~/.ssh
#pip install bokku --upgrade
# Now import your SSH key using setup:ssh
systemctl start uwsgi-bokku
#bokku init