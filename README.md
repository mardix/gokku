# Gokku

A very small PaaS to do git push deployments to your own servers. Supports Python (Flask/Django), Node, PHP and Static HTML, process similar to Heroku

### Features

- Deploy to own server
- SSL with LetsEncrypt
- Instant deploy

---

## On your server

Platform: **Ubuntu 18.04** or latest

The Gokku install.sh script creates a **gokku** user on the system and installs all the necessary packages.

Download the install script from Gokku github, then run the script:

```
curl https://raw.githubusercontent.com/mardix/gokku/master/install.sh > install.sh
chmod 755 install.sh
./install.sh
```

---

## Application 

### Git Remote 

1.Make sure you have GIT on your machine, initialize the application repo

```
git init
git add . 
git commit 
```

2.Add a remote named **gokku** with the username **gokku** and substitute example.com with the public IP address of your Linode

format: `git remote add gokku gokku@[HOST]:[APP_NAME]`

Example

```
git remote add gokku gokku@example.com:flask-example
```

### Deploy application

Once you are ready to deploy, push your code to master

`git push gokku master`


---

## app.json

`app.json` is a manifest format for describing web apps. It declares environment variables, scripts, and other information required to run an app on your server. This document describes the schema in detail.


```json

app.json

{
  "name": "",
  "version": "",
  "description": "",
  "gokku": {
    "env": {
      "server_name": "",
      "runtime": "python",
      "python_version": "2",
      "node_version": "",
      "auto_restart": true,
      "static_paths": ["/dir:path"],
      "https_only": false,
    },
    "scripts": {
      "release": [],
      "destroy": [],
      "predeploy": [],
      "postdeploy": []
    },    
    "run": {
      "web": "app:app",
      "worker": "",
      "worker1": "",
      "worker2": ""
    }
  }
}

```

---

## Credit 

Gokku is a fork of **Piku** https://github.com/piku/piku. Great work and Thank you 

---

## CHANGELOG

- 0.1.0
  - Initial
  - app.json contains the application configuration
  - 'app.run.web' is set for static/web/wsgi command. Static accepts one path
  - added 'cli.upgrade' to upgrade to the latest version
  - 'app.json' can now have scripts to run 
  - 'uwsgi' and 'nginx' are hidden, 'app.env' can contain basic key
  - 'app.env.static_paths' is an array
  - Fixed python virtualenv setup, if the repo was used for a different runtime
  - Simplifying "web" worker. No need for static or wsgi.
  - Python default to wsgi worker, to force to a standalone set env.wsgi: false
  - reformat uwsgi file name '${app-name}___${kind}.${index}.ini' (3 underscores)
  - static sites have their own directives
  - combined static html & php
  - Support languages: Python, Static HTML, PHP
---

License: MIT - Copyright 2019-Forever Mardix

