# Gokku

A very small PaaS to do git push deployments to your own servers. Supports Python (Flask/Django), Node, PHP and Static HTML, process similar to Heroku

### Features

- Deploy to own server
- SSL with LetsEncrypt
- Instant deploy
- Native app languages: Python, Node, PHP, HTML/Static site
- Metrics

### Requirements
- Fresh server
- SSH to server with root access
- Ubuntu 18.04

### Languages

- [x] Python 
- [x] Nodejs
- [x] Static HTML
- [x] PHP
- [x] Any shell script


### Commands

```
  apps     List all apps: [apps]
  config   Show config: [config <app>]
  config   live configuration: [config <app>]
  deploy   Deploy app: [deploy <app>]
  destroy  Destroy app: [destroy <app>]
  init     Initialize environment
  logs     Read tail logs: [logs <app>]
  ps       Show process count: [ps <app>]
  restart  Restart app: [restart <app>]
  scale    Scale processes: [<app> [<proc>=<count>,...
  set      Set config: [set <app> [{KEY1}={VAL1}, ...]]
  set-ssh  Set up a new SSH key (use - for stdin)
  stop     Stop app: [stop <app>]
  unset    Unset config: [unset <app> {KEY}]
  upgrade  Upgrade to the latest version of Gokku
  version  Get Version
```
---

## Setup

### 1. Install On Server/Remote machine

To start off, install Gokku on the server/remote machine.

The Gokku install.sh script creates a **gokku** user on the system and installs all the necessary packages.

Download the install script from Gokku github, then run the script:

```
curl https://raw.githubusercontent.com/mardix/gokku/master/install.sh > install.sh
chmod 755 install.sh
./install.sh
```


### 2. Prepare application on local environement 

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

### 3. Edit app.json

At a minimum, the `app.json` should look like this. 
If the root directory contains `requirements.txt` it will use Python, `package.json` will use Node, else it will use it as STATIC site to serve HTML & PHP. 


```js
// app.json 

{
  "gokku": {
    "env": {
      "domain_name": "mysite.com",
      "runtime": "python"
    },
    "run": {
      "web": "app:app"
    }
  }
}

```

### 4. Deploy application

Once you are ready to deploy, push your code to master

`git push gokku master`


---

## app.json

`app.json` is a manifest format for describing web apps. It declares environment variables, scripts, and other information required to run an app on your server. This document describes the schema in detail.

*(scroll down for a full app.json without the comments)*


```js 
// app.json

{
  "name": "", // name
  "version": "", // version
  "description": "", // description

  // gokku: GOKKU specific configuration
  "gokku": {

    // env: environment variables 
    "env": {
      // domain_name (string): the server name without http
      "domain_name": "",
      // runtime: python|node|static|shell
      // python for wsgi application (default python)
      // node: for node application, where the command should be ie: 'node inde.js 2>&1 | cat'
      // static: for HTML/Static page and PHP
      // shell: for any script that can be executed via the shell script, ie: command 2>&1 | cat
      "runtime": "python",
      // runtime_version: python : 3(default)|2, node: node version
      "runtime_version": "3",
      // auto_restart (bool): to force server restarts when deploying
      "auto_restart": false,
      // static_paths (array): specify list of static path to expose, [/url:path, ...]
      "static_paths": ["/url:path", "/url2:path2"],
      // https_only (bool): when true, it will redirect http to https
      "https_only": true,
      // threads (int): The total threads to use
      "threads": "4",
      // wsgi (bool): if runtime is python by default it will use wsgi, if false it will fallback to the command provided
      "wsgi": true,
      // letsencrypt (bool)
      "letsencrypt": true,

      // nginx (object): nginx specific config. can be omitted
      "nginx": {
        "cloudflare_acl": false,
        "include_file": ""
      },  

      // uwsgi (object): uwsgi specific config. can be omitted
      "uwsgi": {
        "gevent": false,
        "asyncio": false
      }    
    },

    // scripts to run during application lifecycle
    "scripts": {
      // release (array): commands to execute each time the application is released/pushed
      "release": [],
      // destroy (array): commands to execute when the application is being deleted
      "destroy": [],
      // predeploy (array): commands to execute before spinning the app
      "predeploy": [],
      // postdeploy (array): commands to execute after spinning the app
      "postdeploy": []
    },

    // run: processes to run. 
    // 'web' is special, it’s the only process type that can receive external HTTP traffic  
    // all other process name will be regular worker. The name doesn't matter 
    "run": {
      // web (string): it’s the only process type that can receive external HTTP traffic
      // -> app:app (for python using wsgi)
      // -> node server.js 2>&1 cat (For other web app which requires a server command)
      // -> /web-root-dir-name (for static html+php)
      "web": "",

      // worker* (string): command to run, with a name. The name doesn't matter.
      // it can be named anything
      "worker": ""
    }
  }
}

```

### [app.json] without the comments:

Copy and edit the config below in your `app.json` file.

```json

{
  "name": "",
  "version": "",
  "description": "",
  "gokku": {
    "env": {
      "domain_name": "",
      "runtime": "static",
      "runtime_version": "3",
      "auto_restart": true,
      "static_paths": [],
      "https_only": true,
      "threads": 4,
      "wsgi": true,
      "letsencrypt": true,
      "nginx": {
        "cloudflare_acl": false,
        "include_file": ""
      },  
      "uwsgi": {
        "gevent": false,
        "asyncio": false
      }    
    },
    "scripts": {
      "release": [],
      "destroy": [],
      "predeploy": [],
      "postdeploy": []
    },    
    "run": {
      "web": "/",
      "worker": ""
    }
  }
}

```
---

## Credit 

Gokku is a fork of **Piku** https://github.com/piku/piku. Great work and Thank you 

---

## Alternatives

- [Dokku](https://github.com/dokku/dokku)
- [Piku](https://github.com/piku/piku)
- [Caprover](https://github.com/CapRover/CapRover)

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
  - reformat uwsgi file name '{app-name}___{kind}.{index}.ini' (3 underscores)
  - static sites have their own directives
  - combined static html & php
  - Support languages: Python(2, 3), Node, Static HTML, PHP
  - simplify command name
  - added metrics
  - [x] letsencrypt?


---

License: MIT - Copyright 2019-Forever Mardix

