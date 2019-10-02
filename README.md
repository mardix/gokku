# Ruki

A nano Paas to deploy Flask/Django, Node, PHP, Go application and Static HTML sites using GIT, similar to Heroku

## Setup

```
curl https://raw.githubusercontent.com/mardix/ruki/master/bootstrap.sh > bootstrap.sh
chmod 755 bootstrap.sh
./bootstrap.sh
```

#### Note

Ruki requires Python3. The `bootstrap.sh` by default will install it.

or

To do it manually `pip3 install ruki`


###

```
git remote add ruki booku@[HOST]:[APP_NAME]
```

`(ie: git remote add ruki ruki@host.com:mysite.com)`

---

## Usage

### app.json

``` json
app.json

{
  "name": "",
  "version": "",
  "description": "",
  "ruki": {
    "type": "python",
    "python_version": "2",
    "node_version": "",
    "auto_restart": true,
    "nginx": {
      "server_name": "",
      "https_only": "",
      "cloudflare_acl": false,
      "include_file": "",
      "static_paths": ["/dir:path"]
    },
    "uwsgi": {},
    "scripts": {
      "setup": [
        "apt-get install something something -y"
      ],
      "release": [],
      "before_deploy": [],
      "after_deploy": []
    },    
    "run": {
      "web": "manage.py",
      "worker": "",
      "worker2": "",
      "worker3": ""
    }
  }
}

```

---


License: MIT - Copyright 2019-Forever Mardix

