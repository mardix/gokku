# APP.json

```js 
{
  "name": "", // name
  "version": "", // version
  "description": "", // description

  // `gokku` GOKKU specific configuration
  "gokku": {

    // `env` environment variables 
    "env": {
      // server_name (string): the server name without http
      "server_name": "",
      // runtime: python|node|go|static
      "runtime": "python",
      // python_version: if runtime is python, specify python version: 3|2
      "python_version": "3",
      // node_version: if runtime is node, specify node version
      "node_version": "",
      // auto_restart (bool): to force server restarts when deploying
      "auto_restart": false,
      // static_paths (array): specify list of static path to expose, [/url:path, ...]
      "static_paths": ["/url:path", "/url2:path2", "(alias to nginx.static_paths)"],
      // https_only (bool): when true, it will redirect http to https
      "https_only": true,
      // threads (int): The total threads to use
      "threads": "4 (alias to uwsgi.threads)",
      // wsgi (bool): if runtime is python by default it will use wsgi, if false it will fallback to the command provided
      "wsgi": true,

      // nginx (object): nginx specific config. can be omitted
      "nginx": {
        "https_only": "",
        "cloudflare_acl": false,
        "include_file": ""
      },  

      // uwsgi (object): uwsgi specific config. can be omitted
      "uwsgi": {
        "threads": "4",
        "gevent": true,
        "asyncio": true
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
      // -> app:app (for wsgi/python application)
      // -> node server.js (For other web app which requires a server command)
      // -> /web-root-dir-name (for static html+php)
      "web": "",

      // worker* (string): command to run, with a name. The name doesn't matter
      "worker": ""
    }
  }
}

```