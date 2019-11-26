# Gokku

An extremly tiny PaaS (platform as a s service) to deploy multiple apps on a single servers  with git, similar to Heroku or Dokku. 

It is simple and compatible with current infrastucture. 

It supports Python (Flask/Django), Nodejs, PHP and Static HTML.




### Features

- Easy command line setup
- Instant deploy with Git
- Multi applications deployment
- App management: deploy, stop, delete, scale, logs apps
- Simple and straight forward
- SSL/HTTPS with LetsEncrypt
- Any languages: Python, Nodejs, PHP, HTML/Static
- Supports any Shell script, therefore any other languages are supported
- Metrics to see app's health
- Create static sites
- Support Flask, Django, Express, etc...
- Easy configuration with app.json
- Nginx
- Logs

### Requirements

- Fresh server
- SSH to server with root access
- Ubuntu 18.04

### Languages Supported

- [x] Python 
- [x] Nodejs
- [x] Static HTML
- [x] PHP
- [x] Any shell script


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
    "domain_name": "mysite.com",
    "runtime": "python",
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

## Commands

Gokku communicates with your server via SSH, with the user name: `gokku`  

ie: `ssh gokku@host.com`

### General

#### List all commands

List all commands

```
ssh gokku@host.com
```

#### apps

List  all apps

```
ssh gokku@host.com apps
```

#### deploy

Deploy app. `$app_name` is the app name

```
ssh gokku@host.com deploy $app_name
```

#### reload

Reload an app

```
ssh gokku@host.com reload $app_name
```

#### stop

Stop an app

```
ssh gokku@host.com stop $app_name
```

#### destroy

Delete an app

```
ssh gokku@host.com destroy $app_name
```

#### reload-all

Reload all apps on the server

```
ssh gokku@host.com reload-all
```

#### stop-all

Stop all apps on the server

```
ssh gokku@host.com stop-all
```

### Scaling

To scale the application

### ps

Show the process count

```
ssh gokku@host.com ps $app_name
```

### scale

Scale processes

```
ssh gokku@host.com scale $app_name $proc=$count $proc2=$count2
```

ie: `ssh gokku@host.com scale site.com web=4`

### Environment

To edit application's environment variables 

#### env

Show ENV configuration for app

```
ssh gokku@host.com env $app_name
```

#### set

Set ENV config

```
ssh gokku@host.com del $app_name $KEY=$VAL $KEY2=$VAL2
```

#### del

Delete a key from the environment var

```
ssh gokku@host.com del $app_name $KEY
```

### Log

To view application's log

```
ssh gokku@host.com log $app_name
```

### Update

To update Gokku to the latest from Github

```
ssh gokku@host.com update
```

### Version

To get Gokku's version

```
ssh gokku@host.com version
```

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
    // https_only (bool): when true (default), it will redirect http to https
    "https_only": true,
    // threads (int): The total threads to use
    "threads": "4",
    // wsgi (bool): if runtime is python by default it will use wsgi, if false it will fallback to the command provided
    "wsgi": true,
    // letsencrypt (bool) true(default)
    "ssl_letsencrypt": true,

    // nginx (object): nginx specific config. can be omitted
    "nginx": {
      "cloudflare_acl": false,
      "include_file": ""
    },  

    // uwsgi (object): uwsgi specific config. can be omitted
    "uwsgi": {
      "gevent": false,
      "asyncio": false
    },

    // env, custom environment variable
    "env": {

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
    "domain_name": "",
    "runtime": "static",
    "runtime_version": "3",
    "auto_restart": true,
    "static_paths": [],
    "https_only": true,
    "threads": 4,
    "wsgi": true,
    "ssl_letsencrypt": true,
    "nginx": {
      "cloudflare_acl": false,
      "include_file": ""
    },  
    "uwsgi": {
      "gevent": false,
      "asyncio": false
    },    
    "env": {

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

## Multiple Apps Deployment 

**Gokku** allows multiple sites deployment on a single repo.

If you have a mono repo and want to deploy multiple applications based on the domain name, you can do so by having *app.json:gokku* as an array instead of an object. The `app_name` must match the `domain_name` from the *app.json:gokku array*

### Examples

#### Config

Add multiple domains

```json
{
  "gokku": [{
    "domain_name": "mysite.com",
      ...
    },
    {
      "domain_name": "myothersite.com",
      ...
    },
    ...
  ]
}

```
#### Setup GIT

```
git remote add gokku-mysite gokku@example.com:mysite.com
```

```
git remote add gokku-myothersite gokku@other-example.com:myothersite.com
```

#### Deploy app

`git push gokku-mysite master` will deploy *mysite.com*

`git push gokku-myothersite master` will deploy *myothersite.com*

---

## Upgrade Gokku

If you're already using Gokku, you can upgrade Gokku with: 

```
ssh gokku@host.com update
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

- 0.2.0
  - Multiple domain name deployment.
    Sites in Mono repo can now rely on different config based on the app name
    by having app.gooku as a list of dict, it will test for 'domain_name' to match the app_name
    ``` 
    gooku : [
      {"domain_name": "abc.com", ...},
      {"domain_name": "xyz.com", ...},
    ]
    ```
- 0.1.0
  - Initial
  - app.json contains the application configuration
  - 'app.run.web' is set for static/web/wsgi command. Static accepts one path
  - added 'cli.upgrade' to upgrade to the latest version
  - 'app.json' can now have scripts to run 
  - 'uwsgi' and 'nginx' are hidden, 'app.env' can contain basic key
  - 'app.static_paths' is an array
  - Fixed python virtualenv setup, if the repo was used for a different runtime
  - Simplifying "web" worker. No need for static or wsgi.
  - Python default to wsgi worker, to force to a standalone set env.wsgi: false
  - reformat uwsgi file name '{app-name}___{kind}.{index}.ini' (3 underscores)
  - static sites have their own directives
  - combined static html & php
  - Support languages: Python(2, 3), Node, Static HTML, PHP
  - simplify command name
  - added metrics
  - Letsencrypt
  - ssl default
  - https default

---

## TODO

- [x] (0.2.0) Allow multiple site deployment. For multi sites, instead of app.gokku being an object, gooku will be an array with all the site. 'domain_name' should match the app in git. 
ie: gokku@example.com:api.com, gokku@example.com:dev.api.com; with api.com and dev.api.com being two domain_name in the config

---

License: MIT - Copyright 2020-Forever Mardix

