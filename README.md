# Gokku

A nano Paas to deploy Flask/Django, Node, PHP, Go application and Static HTML sites using GIT, similar to Heroku

## Setup

```
curl https://raw.githubusercontent.com/mardix/gokku/master/bootstrap.sh > bootstrap.sh
chmod 755 bootstrap.sh
./bootstrap.sh
```

#### Note

Gokku requires Python3. The `bootstrap.sh` by default will install it.

or

To do it manually `pip3 install gokku`


###

```
git remote add gokku booku@[HOST]:[APP_NAME]
```

`(ie: git remote add gokku gokku@host.com:mysite.com)`

---

## Usage

### app.json

``` json
app.json

{
  "name": "",
  "version": "",
  "description": "",
  "gokku": {
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

