# Bokku

A small PAAS to deploy Flask/Django, Node, PHP, Go application and Static HTML sites using GIT, similar to Heroku

## Setup

```
curl https://raw.githubusercontent.com/mardix/bokku/master/bootstrap.sh > bootstrap.sh
chmod 755 bootstrap.sh
./bootstrap.sh
```

#### Note

Bokku requires Python3. The `bootstrap.sh` by default will install it.

To do it manually `pip3 install bokku`

---

## Usage

### app.json

``` json
app.json

{
  "name": "",
  "version": "",
  "description": "",
  "bokku": {
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

