"Koka Micro-PaaS"

from fcntl import fcntl, F_SETFL, F_GETFL

import os
import re
import pwd
import grp
import sys
import glob
import json
import stat
import time 
import click
import shutil
import socket
import tempfile
import traceback
import collections
import multiprocessing
try:
    from urllib.request import urlopen
except Exception as e:
    from urllib import urlopen
from os.path import abspath, basename, dirname, exists, getmtime, join, realpath, splitext
from subprocess import call, check_output, Popen, STDOUT, PIPE 

from os import chmod, stat, O_NONBLOCK
from socket import socket, AF_INET, SOCK_STREAM
from sys import argv, stdin, stdout, stderr, version_info, exit






# === Make sure we can access all system binaries ===

if 'sbin' not in os.environ['PATH']:
    os.environ['PATH'] = "/usr/local/sbin:/usr/sbin:/sbin:" + os.environ['PATH']

# === Globals - all tweakable settings are here ===
CWD = os.getcwd()

#os.environ["HOME"] = join(CWD, 'devlab', 'HOME')

os.environ["HOME"] = "/home"

KOKA_CMD = "koka"
USER = "koka"
KOKA_ROOT = os.environ.get('KOKA_ROOT', join(os.environ['HOME'],'koka'))
APP_ROOT = abspath(KOKA_ROOT)
DOT_ROOT = abspath(join(KOKA_ROOT, ".koka"))
ENV_ROOT = abspath(join(DOT_ROOT, "envs"))
GIT_ROOT = abspath(join(DOT_ROOT, "repos"))
LOG_ROOT = abspath(join(DOT_ROOT, "logs"))
UWSGI_ROOT = abspath(join(DOT_ROOT, "uwsgi"))
NGINX_ROOT = abspath(join(DOT_ROOT, "nginx"))
CONFIG_FILE_NAME = "app.json"
UWSGI_AVAILABLE = abspath(join(DOT_ROOT, "uwsgi-available"))
UWSGI_ENABLED = abspath(join(DOT_ROOT, "uwsgi-enabled"))
UWSGI_LOG_MAXSIZE = '1048576'
ACME_ROOT = os.environ.get('ACME_ROOT', join(os.environ['HOME'],'.acme.sh'))
ACME_WWW = abspath(join(DOT_ROOT, "acme"))

VALID_RUNTIME = ["python", "node", "static", "php"]
DEFAULT_PACKAGES = []

# pylint: disable=anomalous-backslash-in-string
NGINX_TEMPLATE = """
upstream $APP {
  server $NGINX_SOCKET;
}
server {
  listen              $NGINX_IPV6_ADDRESS:80;
  listen              $NGINX_IPV4_ADDRESS:80;

  location ^~ /.well-known/acme-challenge {
    allow all;
    root ${ACME_WWW};
  }

$INTERNAL_NGINX_COMMON
}
"""

NGINX_HTTPS_ONLY_TEMPLATE = """
upstream $APP {
  server $NGINX_SOCKET;
}
server {
  listen              $NGINX_IPV6_ADDRESS:80;
  listen              $NGINX_IPV4_ADDRESS:80;
  server_name         $NGINX_SERVER_NAME;

  location ^~ /.well-known/acme-challenge {
    allow all;
    root ${ACME_WWW};
  }

  return 301 https://$server_name$request_uri;
}

server {
$INTERNAL_NGINX_COMMON
}
"""
# pylint: enable=anomalous-backslash-in-string

NGINX_COMMON_FRAGMENT = """
  listen              $NGINX_IPV6_ADDRESS:$NGINX_SSL;
  listen              $NGINX_IPV4_ADDRESS:$NGINX_SSL;
  ssl                 on;
  ssl_certificate     $NGINX_ROOT/$APP.crt;
  ssl_certificate_key $NGINX_ROOT/$APP.key;
  server_name         $NGINX_SERVER_NAME;

  # These are not required under systemd - enable for debugging only
  # access_log        $LOG_ROOT/$APP/access.log;
  # error_log         $LOG_ROOT/$APP/error.log;
  
  # Enable gzip compression
  gzip on;
  gzip_proxied any;
  gzip_types text/plain text/xml text/css application/x-javascript text/javascript application/xml+rss application/atom+xml;
  gzip_comp_level 7;
  gzip_min_length 2048;
  gzip_vary on;
  gzip_disable "MSIE [1-6]\.(?!.*SV1)";
  
  # set a custom header for requests
  add_header X-Deployed-By Koka;

  $INTERNAL_NGINX_CUSTOM_CLAUSES

  $INTERNAL_NGINX_STATIC_MAPPINGS

  $INTERNAL_NGINX_PORTMAP
"""

NGINX_PORTMAP_FRAGMENT = """
  location    / {
    $INTERNAL_NGINX_UWSGI_SETTINGS
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_set_header X-Request-Start $msec;
    $NGINX_ACL
  }
"""

NGINX_ACME_FIRSTRUN_TEMPLATE = """
server {
  listen              $NGINX_IPV6_ADDRESS:80;
  listen              $NGINX_IPV4_ADDRESS:80;
  server_name         $NGINX_SERVER_NAME;
  location ^~ /.well-known/acme-challenge {
    allow all;
    root ${ACME_WWW};
  }
}
"""

INTERNAL_NGINX_STATIC_MAPPING = """
  location $static_url {
      sendfile on;
      sendfile_max_chunk 1m;
      tcp_nopush on;
      directio 8m;
      aio threads;
      alias $static_path;
  }
"""

INTERNAL_NGINX_UWSGI_SETTINGS = """
    uwsgi_pass $APP;
    uwsgi_param QUERY_STRING $query_string;
    uwsgi_param REQUEST_METHOD $request_method;
    uwsgi_param CONTENT_TYPE $content_type;
    uwsgi_param CONTENT_LENGTH $content_length;
    uwsgi_param REQUEST_URI $request_uri;
    uwsgi_param PATH_print $document_uri;
    uwsgi_param DOCUMENT_ROOT $document_root;
    uwsgi_param SERVER_PROTOCOL $server_protocol;
    uwsgi_param REMOTE_ADDR $remote_addr;
    uwsgi_param REMOTE_PORT $remote_port;
    uwsgi_param SERVER_ADDR $server_addr;
    uwsgi_param SERVER_PORT $server_port;
    uwsgi_param SERVER_NAME $server_name;
"""

# === Utility functions ===

def _print(message, type="info", arrow=False):
    color = "white"
    types = {
        "default": "white",
        "info": "white",
        "warning": "yellow",
        "error": "red",
        "success": "green"
    }
    color = types[type] if type in types else types["default"]
    msg = "-----> %s" % message if arrow else message
    click.secho(msg, fg=color)

def _call(cmd, cwd=None, env=None, shell=True):
    return call(cmd, cwd=cwd, env=env, shell=shell)

def which(pgm):
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = join(p,pgm)
        if os.path.exists(p) and os.access(p,os.X_OK):
            return p

def sanitize_app_name(app):
    """Sanitize the app name and build matching path"""   
    return "".join(c for c in app if c.isalnum() or c in ('.','_')).rstrip().lstrip('/')

def exit_if_invalid(app):
    """Utility function for error checking upon command startup."""
    app = sanitize_app_name(app)
    if not exists(join(APP_ROOT, app)):
        _print("Error: app '{}' not found.".format(app), type="error")
        exit(1)
    return app

def generate_random_port():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(("",0))
    port = s.getsockname()[1]
    s.close()
    return port

def write_config(filename, bag, separator='='):
    """Helper for writing out config files"""
    with open(filename, 'w') as h:
        for k, v in bag.items():
            h.write('{k:s}{separator:s}{v}\n'.format(**locals()))

def apt_update():
    _print("apt-get UPDATE", arrow=True)
    #_call("sudo apt-get -y update")

def apt_install_packages():
    pkgs = ['bc', 'git', 'build-essential', 'libpcre3-dev', 'zlib1g-dev', 'python-dev', 'python3', 'python3-pip',
            'python3-dev', 'python-pip', 'python-setuptools', 'python3-setuptools', 'nginx', 'incron', 'acl']
    pkgs = " ".join(pkgs)
    _print("apt-get INSTALL '%s'" % pkgs, arrow=True)
    #_call("sudo apt-get -y install %s" % pkgs)

def install_acme_sh():
    """ Install acme.sh for letsencrypt """
    if os.path.isdir(ACME_ROOT):
        return
    try:
        _print("Installing acme.sh", type="success", arrow=True)
        dest = join(KOKA_ROOT, "acme.sh")
        url = "https://raw.githubusercontent.com/Neilpang/acme.sh/master/acme.sh"
        content = urlopen(url).read().decode("utf-8")
        with open(dest, "w") as f:
            f.write(content)
        os.chmod(dest, 0755)
        _call("./acme.sh --install", cwd=KOKA_ROOT, shell=True)
        os.remove(dest)
    except Exception as e:
        _print('Unable to download acme.sh: %s' % e, type="error") 


def setup_authorized_keys(ssh_fingerprint, script_path, pubkey):
    """Sets up an authorized_keys file to redirect SSH commands"""
    
    authorized_keys = join(os.environ['HOME'],'.ssh','authorized_keys')
    if not exists(dirname(authorized_keys)):
        os.makedirs(dirname(authorized_keys))
    # Restrict features and force all SSH commands to go through our script 
    with open(authorized_keys, 'a') as h:
        h.write("""command="FINGERPRINT={ssh_fingerprint:s} NAME=default {script_path:s} $SSH_ORIGINAL_COMMAND",no-agent-forwarding,no-user-rc,no-X11-forwarding,no-port-forwarding {pubkey:s}\n""".format(**locals()))
    os.chmod(dirname(authorized_keys), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    os.chmod(authorized_keys, stat.S_IRUSR | stat.S_IWUSR)

def parse_procfile(filename):
    """Parses a Procfile and returns the worker types. Only one worker of each type is allowed."""
    if not os.path.isfile(filename):
        return None
    workers = {}
    with open(filename, 'r') as procfile:
        for line in procfile:
            try:
                kind, command = map(lambda x: x.strip(), line.split(":", 1))
                workers[kind] = command
            except:
                _print("Warning: unrecognized Procfile entry '{}'".format(line), type="warning")
    return workers 


def expand_vars(buffer, env, default=None, skip_escaped=False):
    """expand shell-style environment variables in a buffer"""
    def replace_var(match):
        return env.get(match.group(2) or match.group(1), match.group(0) if default is None else default)
    pattern = (r'(?<!\\)' if skip_escaped else '') + r'\$(\w+|\{([^}]*)\})'
    return re.sub(pattern, replace_var, buffer)


def get_cmd_output(cmd):
    """executes a command and grabs its output, if any"""
    try:
        env = environ
        return str(check_output(cmd, stderr=STDOUT, env=env, shell=True))
    except:
        return ""


def read_settings_file(filename, env={}):
    """Parses a settings file and returns a dict with environment variables"""
    if not os.path.isfile(filename):
        return {}
    with open(filename, 'r') as settings:
        for line in settings:
            try:
                if '#' == line[0] or len(line.strip()) == 0: # ignore comments and newlines
                    continue                
                k, v = map(lambda x: x.strip(), line.split("=", 1))
                env[k] = expand_vars(v, env)
            except:
                _print("Error: malformed setting '{}', ignoring file.".format(line), type="error")
                return {}
    return env


def has_bin_dependencies(binaries):
    """Checks if all the binaries exist and are executable"""
    _print("Checking requirements: {}".format(binaries), type='success', arrow=True)
    requirements = list(map(which, binaries))
    _print(str(requirements))
    return False if None in requirements else True

def get_app_config(app):
    config_file = join(APP_ROOT, app, CONFIG_FILE_NAME)
    with open(config_file) as f:
        return json.load(f)["koka"]
    return None

def get_app_proc(app):
    return get_app_config(app)["run"]

def get_app_env(app):
    env = {}
    config = get_app_config(app)
    for k, v in config.items():
        if k not in ["run", "scripts"]:
            if isinstance(v, dict):
                env.update({("%s_%s" % (k, vk)).upper(): vv for vk, vv in v.items() })
            else:
                env[k.upper()] = v
    return env

def to_proc_env(config):
    env = {}
    for k in ["nginx", "uswgi"]:
        if config.get(k):
            for l in config.get(k):
                m = ("%s_%s" % (k, l)).upper()
                env[m] = config.get(k).get(l)
    return env


def get_app_runtime(app):
    app_path = join(APP_ROOT, app)
    config = get_app_config(app);
    app_runtime = config.get("type")
    
    if app_runtime.lower() in VALID_RUNTIME:
        return app_runtime.lower()

    if exists(join(app_path, 'requirements.txt')):
        return "python"
    elif exists(join(app_path, 'package.json')) and has_bin_dependencies(['nodejs', 'npm']):
        return "node"        
    elif exists(join(app_path, 'composer.json')):
        return "php"        
    return None
    
def do_deploy(app, deltas={}, newrev=None):
    """Deploy an app by resetting the work directory"""
    
    app_path = join(APP_ROOT, app)
    cwd = join(APP_ROOT, app)
    log_path = join(LOG_ROOT, app)
    config = get_app_config(app)

    env = {'GIT_WORK_DIR': app_path}
    if exists(app_path):
        _print("Deploying app '{}'".format(app), type="success", arrow=True)
        _call('git fetch --quiet', cwd=app_path, env=env, shell=True)
        if newrev:
            _call('git reset --hard {}'.format(newrev), cwd=app_path, env=env, shell=True)
        _call('git submodule init', cwd=app_path, env=env, shell=True)
        _call('git submodule update', cwd=app_path, env=env, shell=True)

        if not config:
            _print("Error: Invalid app.json for app '{}'.".format(app), type="error")
        else:
            if not os.path.isdir(log_path):
                os.makedirs(log_path)

            app_runtime = get_app_runtime(app)
            if not app_runtime:
                _print("Could not detect runtime!", arrow=True, type="error")
            else:
                _print("[%s] app detected." % app_runtime, arrow=True, type="success")

                env_path = join(ENV_ROOT, app)
                if not exists(env_path):
                    os.makedirs(env_path)

                # python
                if app_runtime == "python":
                    deploy_python(app, deltas)
                # node
                elif app_runtime == "node":
                    deploy_node(app, deltas)
                # php
                elif app_runtime == "php":
                    deploy_php(app, deltas)                    
                # static
                elif app_runtime == "static":
                    deploy_static(app, deltas)

    else:
        _print("Error: app '%s' not found." % app, type="error")


def run_app_scripts(app, script_type, env=None):
    cwd = join(APP_ROOT, app)
    config = get_app_config(app)
    if "scripts" in config and script_type in config["scripts"]:
        _print("Running scripts: %s ..." % script_type, arrow=True)
        for cmd in config["scripts"][script_type]:
            _call(cmd, cwd, env=env)

def deploy_python(app, deltas={}):
    """Deploy a Python application"""
    
    cwd = join(APP_ROOT, app)
    virtualenv_path = join(ENV_ROOT, app)
    requirements = join(APP_ROOT, app, 'requirements.txt')
    env_file = join(APP_ROOT, app, 'ENV')
    # Peek at environment variables shipped with repo (if any) to determine version
    env = {}
    if exists(env_file):
        env.update(parse_procfile(env_file, env))

    version = int(env.get("PYTHON_VERSION", "3"))

    first_time = False
    if not exists(virtualenv_path):
        _print("Creating virtualenv for '{}'".format(app), type="success")
        os.makedirs(virtualenv_path)
        _call('virtualenv --python=python{version:d} {app:s}'.format(**locals()), cwd=ENV_ROOT)
        first_time = True

    activation_script = join(virtualenv_path,'bin','activate_this.py')
    #exec(open(activation_script).read(), dict(__file__=activation_script))

    if first_time or getmtime(requirements) > getmtime(virtualenv_path):
        _print("Running pip install...", type="success", arrow=True)
        _call('pip install -r %s' % requirements, cwd=cwd)

    run_app_scripts(app, "before_deploy")
    spawn_app(app, deltas)
    run_app_scripts(app, "after_deploy")

def deploy_node(app, deltas={}):
    """Deploy a Node  application"""

    virtualenv_path = join(ENV_ROOT, app)
    node_path = join(ENV_ROOT, app, "node_modules")
    node_path_tmp = join(APP_ROOT, app, "node_modules")
    env_file = join(APP_ROOT, app, CONFIG_FILE_NAME)
    deps = join(APP_ROOT, app, 'package.json')

    first_time = False
    if not exists(node_path):
        _print("Creating node_modules for '{}'".format(app),  arrow=True)
        os.makedirs(node_path)
        first_time = True

    env = {
        'VIRTUAL_ENV': virtualenv_path,
        'NODE_PATH': node_path,
        'NPM_CONFIG_PREFIX': abspath(join(node_path, "..")),
        "PATH": ':'.join([join(virtualenv_path, "bin"), join(node_path, ".bin"),os.environ['PATH']])
    }
    if exists(env_file):
        env.update(read_settings_file(env_file))

    version = env.get("NODE_VERSION")
    node_binary = join(virtualenv_path, "bin", "node")
    installed = check_output("{} -v".format(node_binary), cwd=join(APP_ROOT, app), env=env, shell=True).decode("utf8").rstrip("\n") if exists(node_binary) else ""

    if version and has_bin_dependencies(['nodeenv']):
        if not installed.endswith(version):
            started = glob.glob(join(UWSGI_ENABLED, '{}*.ini'.format(app)))
            if installed and len(started):
                _print("Warning: Can't update node with app running. Stop the app & retry.", type="warning")
            else:
                _print("Installing node version '{NODE_VERSION:s}' using nodeenv".format(**env), type="success", arrow=TreeBuilder(element_factory=None))
                _call("nodeenv --prebuilt --node={NODE_VERSION:s} --clean-src --force {VIRTUAL_ENV:s}".format(**env), cwd=virtualenv_path, env=env, shell=True)
        else:
            _print("Node is installed at {}.".format(version), arrow=True)

    if exists(deps) and has_bin_dependencies(['npm']):
        if first_time or getmtime(deps) > getmtime(node_path):
            _print("Running npm for '{}'".format(app), type="success", arrow=True)
            os.symlink(node_path, node_path_tmp)
            _call('npm install', cwd=join(APP_ROOT, app), env=env, shell=True)
            os.unlink(node_path_tmp)
    
    run_app_scripts(app, "before_deploy")
    spawn_app(app, deltas)
    run_app_scripts(app, "after_deploy")

def deploy_php(app, deltas={}):
    pass

def deploy_static(app, deltas={}):
    return spawn_app(app, deltas)


def spawn_app(app, deltas={}):
    """Create all workers for an app"""
    
    cwd = join(APP_ROOT, app)
    config = get_app_config(app)
    proc = get_app_proc(app) 
    
    ordinals = collections.defaultdict(lambda:1)
    worker_count = {k:1 for k in proc.keys()}

    # the Python virtualenv
    virtualenv_path = join(ENV_ROOT, app)
    # Settings shipped with the app
    env_file = join(APP_ROOT, app, CONFIG_FILE_NAME)
    # Custom overrides
    settings = join(ENV_ROOT, app, 'ENV')
    # Live settings
    live = join(ENV_ROOT, app, 'LIVE_ENV')
    # Scaling
    scaling = join(ENV_ROOT, app, 'SCALING')

    env = {
        'APP': app,
        'LOG_ROOT': LOG_ROOT,
        'HOME': os.environ['HOME'],
        'USER': os.environ['USER'],
        'PATH': ':'.join([join(virtualenv_path,'bin'),os.environ['PATH']]),
        'PWD': cwd,
        'VIRTUAL_ENV': virtualenv_path,
    }

    safe_defaults = {
        'NGINX_IPV4_ADDRESS': '0.0.0.0',
        'NGINX_IPV6_ADDRESS': '[::]',
        'BIND_ADDRESS': '127.0.0.1',
    }

    # add node path if present
    node_path = join(virtualenv_path, "node_modules")
    if os.path.isdir(node_path):
        env["NODE_PATH"] = node_path
        env["PATH"] = ':'.join([join(node_path, ".bin"),env['PATH']])

    if "web" in proc:
        env.update(get_app_env(app))

        # Pick a port if none defined
        if 'PORT' not in env:
            env['PORT'] = str(generate_random_port())
            _print("picked free port {PORT}".format(**env),  arrow=True)

        # Safe defaults for addressing     
        for k, v in safe_defaults.items():
            if k not in env:
                _print("nginx {k:s} set to {v}".format(**locals()),  arrow=True)
                env[k] = v
                
        # Set up nginx if we have NGINX_SERVER_NAME set
        if 'NGINX_SERVER_NAME' in env:
            nginx = get_cmd_output("nginx -V")
            nginx_ssl = "443 ssl"
            if "--with-http_v2_module" in nginx:
                nginx_ssl += " http2"
            nginx_conf = join(NGINX_ROOT,"{}.conf".format(app))
        
            env.update({ 
                'NGINX_SSL': nginx_ssl,
                'NGINX_ROOT': NGINX_ROOT,
                'ACME_WWW': ACME_WWW,
            })
            
            proxy_pass = '{BIND_ADDRESS:s}:{PORT:s}'.format(**env)
            env['INTERNAL_NGINX_UWSGI_SETTINGS'] = 'proxy_pass http://%s;' % proxy_pass
            env['NGINX_SOCKET'] = proxy_pass 
            _print("nginx will look for app '{}' on {}".format(app, env['NGINX_SOCKET']), arrow=True)

            domain = env['NGINX_SERVER_NAME'].split()[0]       
            key, crt = [join(NGINX_ROOT, "{}.{}".format(app,x)) for x in ['key','crt']]
            if exists(join(ACME_ROOT, "acme.sh")):
                acme = ACME_ROOT
                www = ACME_WWW
                # if this is the first run there will be no nginx conf yet
                # create a basic conf stub just to serve the acme auth
                if not exists(nginx_conf):
                    _print("writing temporary nginx conf", True)
                    buffer = expand_vars(NGINX_ACME_FIRSTRUN_TEMPLATE, env)
                    with open(nginx_conf, "w") as h:
                        h.write(buffer)
                if not exists(key) or not exists(join(ACME_ROOT, domain, domain + ".key")):
                    _print("getting letsencrypt certificate", True)
                    _call('{acme:s}/acme.sh --issue -d {domain:s} -w {www:s}'.format(**locals()), shell=True)
                    _call('{acme:s}/acme.sh --install-cert -d {domain:s} --key-file {key:s} --fullchain-file {crt:s}'.format(**locals()), shell=True)
                    if exists(join(ACME_ROOT, domain)) and not exists(join(ACME_WWW, app)):
                        os.symlink(join(ACME_ROOT, domain), join(ACME_WWW, app))
                else:
                    _print("letsencrypt certificate already installed")

            # fall back to creating self-signed certificate if acme failed
            if not os.path.isfile(key) or os.stat(crt).st_size == 0:
                _print("generating self-signed certificate")
                _call('openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/C=US/ST=NY/L=New York/O=Koka/OU=Self-Signed/CN={domain:s}" -keyout {key:s} -out {crt:s}'.format(**locals()), shell=True)
            
            # restrict access to server from CloudFlare IP addresses
            acl = []
            if env.get('NGINX_CLOUDFLARE_ACL') is True:
                try:
                    cf = json.loads(urlopen('https://api.cloudflare.com/client/v4/ips').read().decode("utf-8"))
                    if cf['success'] is True:
                        for i in cf['result']['ipv4_cidrs']:
                            acl.append("allow {};".format(i))
                        for i in cf['result']['ipv6_cidrs']:
                            acl.append("allow {};".format(i))
                        # allow access from controlling machine
                        if 'SSH_CLIENT' in environ:
                            remote_ip = os.environ['SSH_CLIENT'].split()[0]
                            _print("Adding your IP ({}) to nginx ACL".format(remote_ip),  arrow=True)
                            acl.append("allow {};".format(remote_ip))
                        acl.extend(["allow 127.0.0.1;","deny all;"])
                except Exception:
                    cf = collections.defaultdict()
                    _print("Could not retrieve CloudFlare IP ranges: {}".format(traceback.format_exc()),  arrow=True)

            env['NGINX_ACL'] = " ".join(acl)
            env['INTERNAL_NGINX_STATIC_MAPPINGS'] = ''

            # Static url
            # Get a mapping of [/url:path1 , /url2:path2]
            static_paths = env.get('NGINX_STATIC_PATHS', [])
            if len(static_paths):
                try:
                    for item in static_paths:
                        static_url, static_path = item.split(':', 2)
                        if static_path[0] != '/':
                            static_path = join(cwd, static_path)
                        env['INTERNAL_NGINX_STATIC_MAPPINGS'] = env['INTERNAL_NGINX_STATIC_MAPPINGS'] + expand_vars(INTERNAL_NGINX_STATIC_MAPPING, locals())
                except Exception as e:
                    _print("Error {} in static path spec: should be [/url1:path1, /url2:path2, ...], ignoring.".format(e), type="error")
                    env['INTERNAL_NGINX_STATIC_MAPPINGS'] = ''

            env['INTERNAL_NGINX_CUSTOM_CLAUSES'] = expand_vars(open(join(cwd, env["NGINX_INCLUDE_FILE"])).read(), env) if env.get("NGINX_INCLUDE_FILE") else ""
            env['INTERNAL_NGINX_PORTMAP'] = expand_vars(NGINX_PORTMAP_FRAGMENT, env)
            env['INTERNAL_NGINX_COMMON'] = expand_vars(NGINX_COMMON_FRAGMENT, env)

            _print("nginx will map app '{}' to hostname '{}'".format(app, env['NGINX_SERVER_NAME']))
            if 'NGINX_HTTPS_ONLY' in env or 'HTTPS_ONLY' in env:
                buffer = expand_vars(NGINX_HTTPS_ONLY_TEMPLATE, env)
                _print("nginx will redirect all requests to hostname '{}' to HTTPS".format(env['NGINX_SERVER_NAME']))
            else:
                buffer = expand_vars(NGINX_TEMPLATE, env)
            with open(nginx_conf, "w") as h:
                h.write(buffer)
            # prevent broken config from breaking other deploys
            try:
                nginx_config_test = str(check_output("nginx -t 2>&1 | grep {}".format(app), env=environ, shell=True))
            except Exception as e:
                nginx_config_test = None
            if nginx_config_test:
                _print("Error: [nginx config] {}".format(nginx_config_test), type="error")
                _print("Warning: removing broken nginx config.", type="warning")
                os.remove(nginx_conf)

    # Configured worker count
    if exists(scaling):
        worker_count.update({k: int(v) for k,v in parse_procfile(scaling).items() if k in proc})
    
    to_create = {}
    to_destroy = {}    
    for k, v in worker_count.items():
        to_create[k] = range(1,worker_count[k] + 1)
        if k in deltas and deltas[k]:
            to_create[k] = range(1, worker_count[k] + deltas[k] + 1)
            if deltas[k] < 0:
                to_destroy[k] = range(worker_count[k], worker_count[k] + deltas[k], -1)
            worker_count[k] = worker_count[k]+deltas[k]

    # Cleanup env
    for k, v in list(env.items()):
        if k.startswith('INTERNAL_'):
            del env[k]

    # Save current settings
    write_config(live, env)
    write_config(scaling, worker_count, ':')
    
    if env.get("AUTO_RESTART") is True:
        config = glob.glob(join(UWSGI_ENABLED, '{}*.ini'.format(app)))
        if len(config):
            _print("Removing uwsgi configs to trigger auto-restart.", True)
            for c in config:
                os.remove(c)

    # Create new proc
    for k, v in to_create.items():
        for w in v:
            enabled = join(UWSGI_ENABLED, '{app:s}_{k:s}.{w:d}.ini'.format(**locals()))
            if not exists(enabled):
                _print("spawning '{app:s}:{k:s}.{w:d}'".format(**locals()), True)
                spawn_worker(app=app, kind=k, command=proc[k], env=env, ordinal=w)
        
    # Remove unnecessary proc (leave logfiles)
    for k, v in to_destroy.items():
        for w in v:
            enabled = join(UWSGI_ENABLED, '{app:s}_{k:s}.{w:d}.ini'.format(**locals()))
            if exists(enabled):
                _print("terminating '{app:s}:{k:s}.{w:d}'".format(**locals()), arrow=True, type="warning")
                os.remove(enabled)

    return env
    

def spawn_worker(app, kind, command, env, ordinal=1):
    """Set up and deploy a single worker of a given kind"""

    app_runtime = get_app_runtime(app)
    if not app_runtime:
        _print("Could not detect runtime!", arrow=True, type="error")
        return

    cwd = join(APP_ROOT, app)
    config = get_app_config(app)

    if app_runtime == "python":
        kind = "wsgi"
    elif app_runtime == "static":
        kind = "static"
    env['PROC_TYPE'] = kind

    env_path = join(ENV_ROOT, app)
    available = join(UWSGI_AVAILABLE, '{app:s}_{kind:s}.{ordinal:d}.ini'.format(**locals()))
    enabled = join(UWSGI_ENABLED, '{app:s}_{kind:s}.{ordinal:d}.ini'.format(**locals()))
    log_file = join(LOG_ROOT, app, kind)



    settings = [
        ('chdir',               cwd),
        ('master',              'true'),
        ('project',             app),
        ('max-requests',        env.get('UWSGI_MAX_REQUESTS', '1024')),
        ('listen',              env.get('UWSGI_LISTEN', '16')),
        ('processes',           env.get('UWSGI_PROCESSES', '1')),
        ('procname-prefix',     '{app:s}:{kind:s}'.format(**locals())),
        ('enable-threads',      env.get('UWSGI_ENABLE_THREADS', 'true').lower()),
        ('log-x-forwarded-for', env.get('UWSGI_LOG_X_FORWARDED_FOR', 'false').lower()),
        ('log-maxsize',         env.get('UWSGI_LOG_MAXSIZE', UWSGI_LOG_MAXSIZE)),
        ('logto',               '{log_file:s}.{ordinal:d}.log'.format(**locals())),
        ('log-backupname',      '{log_file:s}.{ordinal:d}.log.old'.format(**locals())),
    ]

    # only add virtualenv to uwsgi if it's a real virtualenv
    if exists(join(env_path, "bin", "activate_this.py")):
        settings.append(('virtualenv', env_path))

    if kind == 'wsgi':
        settings.extend([('module', command), ('threads', env.get('UWSGI_THREADS','4'))])

        python_version = int(env.get('PYTHON_VERSION','3'))
        if python_version == 2:
            settings.extend([('plugin','python')])
            if 'UWSGI_GEVENT' in env:
                settings.extend([('plugin','gevent_python'),('gevent',env['UWSGI_GEVENT'])])
            elif 'UWSGI_ASYNCIO' in env:
                settings.extend([('plugin','asyncio_python')])
        elif python_version == 3:
            settings.extend([('plugin','python3'),])
            if 'UWSGI_ASYNCIO' in env:
                settings.extend([('plugin','asyncio_python3'),])
            
        # If running under nginx, don't expose a port at all
        if 'NGINX_SERVER_NAME' in env:
            sock = join(NGINX_ROOT, "%s.sock" % app)
            _print("nginx will talk to uWSGI via {}".format(sock), type="warning", arrow=True)
            settings.extend([('socket', sock), ('chmod-socket', '664')])
        else:
            _ = '{BIND_ADDRESS:s}:{PORT:s}'.format(**env)
            _print("nginx will talk to uWSGI via: %s " % _, type="warning", arrow=True)
            settings.extend([ ('http', _), ('http-socket', _)])
    elif kind == 'web':
        _print("nginx will talk to the 'web' process via {BIND_ADDRESS:s}:{PORT:s}".format(**env), type="waring", arrow=True)
        settings.append(('attach-daemon', command))
    elif kind == 'static':
        _print("nginx serving static files only".format(**env), type="waring", arrow=True)
    else:
        settings.append(('attach-daemon', command))

    if kind in ['wsgi', 'web']:
        settings.append(('log-format','%%(addr) - %%(user) [%%(ltime)] "%%(method) %%(uri) %%(proto)" %%(status) %%(size) "%%(referer)" "%%(uagent)" %%(msecs)ms'))
        
    # remove unnecessary variables from the env in nginx.ini
    for k in ['NGINX_ACL']:
        if k in env:
            del env[k]

    # insert user defined uwsgi settings if set
    settings += read_settings_file(join(APP_ROOT, app, env.get("UWSGI_INCLUDE_FILE"))).items() if env.get("UWSGI_INCLUDE_FILE") else []

    for k, v in env.items():
        settings.append(('env', '{k:s}={v}'.format(**locals())))

    if kind != 'static':
        with open(available, 'w') as h:
            h.write('[uwsgi]\n')
            for k, v in settings:
                h.write("{k:s} = {v}\n".format(**locals()))

        shutil.copyfile(available, enabled)

def do_restart(app):
    config = glob.glob(join(UWSGI_ENABLED, '{}*.ini'.format(app)))

    if len(config):
        _print("Restarting app '{}'...".format(app), type="warning")
        for c in config:
            os.remove(c)
        spawn_app(app)
    else:
        _print("Error: app '%s' not deployed" % app, type="error")


def multi_tail(app, filenames, catch_up=20):
    """Tails multiple log files"""
    
    # Seek helper
    def peek(handle):
        where = handle.tell()
        line = handle.readline()
        if not line:
            handle.seek(where)
            return None
        return line

    inodes = {}
    files = {}
    prefixes = {}
    
    # Set up current state for each log file
    for f in filenames:
        prefixes[f] = splitext(basename(f))[0]
        files[f] = open(f)
        inodes[f] = os.stat(f).st_ino
        files[f].seek(0, 2)
        
    longest = max(map(len, prefixes.values()))
    
    # Grab a little history (if any) 
    for f in filenames:
        for line in collections.deque(open(f), catch_up):
            yield "{} | {}".format(prefixes[f].ljust(longest), line)

    while True:
        updated = False
        # Check for updates on every file
        for f in filenames:
            line = peek(files[f])
            if not line:
                continue
            else:
                updated = True
                yield "{} | {}".format(prefixes[f].ljust(longest), line)
                
        if not updated:
            time.sleep(1)
            # Check if logs rotated
            for f in filenames:
                if exists(f):
                    if os.stat(f).st_ino != inodes[f]:
                        files[f] = open(f)
                        inodes[f] = os.stat(f).st_ino
                else:
                    filenames.remove(f)

# -------------------------------------------------------------------------------------
# === CLI commands ===    
    
@click.group()
def cli():
    """Koka, the smallest PaaS you've ever seen"""
    pass

    
@cli.resultcallback()
def cleanup(ctx):
    """Callback from command execution -- add debugging to taste"""
    pass


# --- User commands ---

@cli.command("apps")
def list_apps():
    """List all apps"""
    
    for a in os.listdir(APP_ROOT):
        if not a.startswith((".", "_")):
            _print(a, type="success")


@cli.command("config")
@click.argument('app')
def cmd_config(app):
    """<app>: Show an app config"""
    
    exit_if_invalid(app)

    app = sanitize_app_name(app)
    config_file = join(ENV_ROOT, app, CONFIG_FILE_NAME)
    if exists(config_file):
        _print(open(config_file).read().strip(), fg='white')
    else:
        _print("Warning: app '{}' not deployed, no config found.".format(app), type="warning")


@cli.command("config-get")
@click.argument('app')
@click.argument('setting')
def cmd_config_get(app, setting):
    """e.g.: koka config:get <app> FOO"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)
    
    config_file = join(ENV_ROOT, app, 'ENV')
    if exists(config_file):
        env = read_settings_file(config_file)
        if setting in env:
            _print("{}".format(env[setting]))
    else:
        _print("Warning: no active configuration for '{}'".format(app), type="warning")


@cli.command("config-set")
@click.argument('app')
@click.argument('settings', nargs=-1)
def cmd_config_set(app, settings):
    """<app> [KEY1=VAL1, ...] - Set config"""
    
    exit_if_invalid(app)
    app  = sanitize_app_name(app)
    
    config_file = join(ENV_ROOT, app, 'ENV')
    env = read_settings_file(config_file)
    for s in settings:
        try:
            k, v = map(lambda x: x.strip(), s.split("=", 1))
            env[k] = v
            _print("Setting {k:s}={v} for '{app:s}'".format(**locals()))
        except:
            _print("Error: malformed setting %s " %s , type="error")
            return
    write_config(config_file, env)
    do_deploy(app)


@cli.command("config-unset")
@click.argument('app')
@click.argument('settings', nargs=-1)
def cmd_config_unset(app, settings):
    """e.g.: koka config:unset <app> FOO"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)
    
    config_file = join(ENV_ROOT, app, 'ENV')
    env = read_settings_file(config_file)
    for s in settings:
        if s in env:
            del env[s]
            _print("Unsetting {} for '{}'".format(s, app))
    write_config(config_file, env)
    do_deploy(app)


@cli.command("config:live")
@click.argument('app')
def cmd_config_live(app):
    """e.g.: koka config:live <app>"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)

    live_config = join(ENV_ROOT, app, 'LIVE_ENV')
    if exists(live_config):
        _print(open(live_config).read().strip())
    else:
        _print("Warning: app '{}' not deployed, no config found.".format(app), type="warning")


@cli.command("deploy")
@click.argument('app')
def cmd_deploy(app):
    """<app>: Deploy an app"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)
    do_deploy(app)


@cli.command("destroy")
@click.argument('app')
def cmd_destroy(app):
    """<app>: Permanently destroy an app"""
    exit_if_invalid(app)
    app = sanitize_app_name(app)
    _print("**** WARNING ****", type="warning")
    _print("**** YOU ARE ABOUT TO DESTROY AN APP ****", type="warning")
    if not click.confirm("Do you want to destroy this app? It will delete everything"):
        exit(1)
    if not click.confirm("Are you really sure?"):
        exit(1)

    for p in [join(x, app) for x in [APP_ROOT, GIT_ROOT, ENV_ROOT, LOG_ROOT]]:
        if exists(p):
            _print("Removing folder '%s'" % p, type="warning")
            shutil.rmtree(p)

    for p in [join(x, '%s*.ini' % app) for x in [UWSGI_AVAILABLE, UWSGI_ENABLED]]:
        g = glob.glob(p)
        for f in g:
            _print("Removing file '{}'".format(f), type="warning")
            os.remove(f)
                
    nginx_files = [join(NGINX_ROOT, "{}.{}".format(app,x)) for x in ['conf','sock','key','crt']]
    for f in nginx_files:
        if exists(f):
            _print("Removing file '{}'".format(f), type="warning")
            os.remove(f)

    acme_link = join(ACME_WWW, app)
    acme_certs = realpath(acme_link)
    if exists(acme_certs):
        _print("Removing folder '{}'".format(acme_certs), type="warning")
        shutil.rmtree(acme_certs)
        _print("Removing file '{}'".format(acme_link), type="warning")
        os.unlink(acme_link)

    
@cli.command("logs")
@click.argument('app')
def cmd_logs(app):
    """<app>: Run tail logs"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)

    logfiles = glob.glob(join(LOG_ROOT, app, '*.log'))
    if len(logfiles):
        for line in multi_tail(app, logfiles):
            _print(line.strip())
    else:
        _print("No logs found for app '{}'.".format(app), type="error")


@cli.command("ps")
@click.argument('app')
def cmd_ps(app):
    """<app>: Show process"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)

    config_file = join(ENV_ROOT, app, 'SCALING')
    if exists(config_file):
        _print(open(config_file).read().strip())
    else:
        _print("Error: no workers found for app '%s'." % app, type="error")


@cli.command("scale")
@click.argument('app')
@click.argument('settings', nargs=-1)
def cmd_ps_scale(app, settings):
    """<app> [<proc>=<count> ...]: Scale process"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)

    config_file = join(ENV_ROOT, app, 'SCALING')
    worker_count = {k:int(v) for k, v in parse_procfile(config_file).items()}
    deltas = {}
    for s in settings:
        try:
            k, v = map(lambda x: x.strip(), s.split("=", 1))
            c = int(v) # check for integer value
            if c < 0:
                _print("Error: cannot scale type '%s' below 0" % k, type="error")
                return
            if k not in worker_count:
                _print("Error: worker type '%s' not present in '%s'" % (k, app), type="error")
                return
            deltas[k] = c - worker_count[k]
        except:
            _print("Error: malformed setting '%s'" % s, type="error")
            return
    do_deploy(app, deltas)


@cli.command("restart")
@click.argument('app')
def cmd_restart(app):
    """<app>: Restart an app"""
    
    exit_if_invalid(app)
    app = sanitize_app_name(app)
    do_restart(app)


@cli.command("stop")
@click.argument('app')
def cmd_stop(app):
    """<app>: Stop an app"""

    exit_if_invalid(app)
    app = sanitize_app_name(app)
    config = glob.glob(join(UWSGI_ENABLED, '{}*.ini'.format(app)))

    if len(config):
        _print("Stopping app '{}'...".format(app), type="warning")
        for c in config:
            os.remove(c)
    else:
        _print("Error: app '{}' not deployed!".format(app), type="error")
       

@cli.command("init")
def cmd_setup():
    """Initialize environment"""

    _print("Running in Python {}".format(".".join(map(str,version_info))))
    
    _print("creating new user: %s" % USER, type="success", arrow=True)
    _call("adduser --disabled-password --gecos 'PaaS access' --ingroup www-data %s" % USER)
        
    # Create required paths
    for p in [APP_ROOT, GIT_ROOT, ACME_WWW, ENV_ROOT, UWSGI_ROOT, UWSGI_AVAILABLE, UWSGI_ENABLED, LOG_ROOT, NGINX_ROOT]:
        if not os.path.isdir(p):
            _print("Creating %s" % p)
            os.makedirs(p)

    # Set up the uWSGI emperor config
    settings = [
        ('chdir',           UWSGI_ROOT),
        ('emperor',         UWSGI_ENABLED),
        ('log-maxsize',     UWSGI_LOG_MAXSIZE),
        ('logto',           join(UWSGI_ROOT, 'uwsgi.log')),
        ('log-backupname',  join(UWSGI_ROOT, 'uwsgi.old.log')),
        ('socket',          join(UWSGI_ROOT, 'uwsgi.sock')),
        ('uid',             pwd.getpwuid(os.getuid()).pw_name),
        ('gid',             grp.getgrgid(os.getgid()).gr_name),
        ('enable-threads',  'true'),
        ('threads',         '{}'.format(multiprocessing.cpu_count() * 2)),
    ]
    with open(join(UWSGI_ROOT,'uwsgi.ini'), 'w') as h:
        h.write('[uwsgi]\n')
        for k, v in settings:
            h.write("{k:s} = {v}\n".format(**locals()))

    # acme
    install_acme_sh()

    # 



@cli.command("setup-ssh")
@click.argument('public_key_file')
def cmd_setup_ssh(public_key_file):
    """Set up a new SSH key (use - for stdin)"""

    def add_helper(key_file):
        if exists(key_file):
            try:
                fingerprint = str(check_output('ssh-keygen -lf ' + key_file, shell=True)).split(' ', 4)[1]
                with open(key_file) as f:
                    key = f.read().strip()
                _print("Adding key '{}'.".format(fingerprint))
                setup_authorized_keys(fingerprint, KOKA_CMD, key)
            except Exception:
                _print("Error: invalid public key file '{}': {}".format(key_file, traceback.format_exc()), type="error")
        elif '-' == public_key_file:
            buffer = "".join(stdin.readlines())
            with tempfile.NamedTemporaryFile(mode="w") as f:
                f.write(buffer)
                f.flush()
                add_helper(f.name)
        else:
            _print("Error: public key file '{}' not found.".format(key_file), type="error")

    add_helper(public_key_file) 
        
# --- Internal commands ---


def git_hook(app):
    """INTERNAL: Post-receive git hook"""
    
    app = sanitize_app_name(app)
    repo_path = join(GIT_ROOT, app)
    app_path = join(APP_ROOT, app)


    #--- Run setup scripts
    # run_app_scripts(app, "setup")


    # for line in stdin:
    #     # pylint: disable=unused-variable
    #     oldrev, newrev, refname = line.strip().split(" ")
    #     # Handle pushes
    #     if not exists(app_path):
    #         _print("-----> Creating app '{}'".format(app))
    #         os.makedirs(app_path)
    #         _call('git clone --quiet {} {}'.format(repo_path, app), cwd=APP_ROOT, shell=True)
    #     do_deploy(app, newrev=newrev)



def git_receive_pack(app):
    """INTERNAL: Handle git pushes for an app"""

    app = sanitize_app_name(app)

    hook_path = join(GIT_ROOT, app, 'hooks', 'post-receive')
    env = globals()
    env.update(locals())

    if not exists(hook_path):
        os.makedirs(dirname(hook_path))
        # Initialize the repository with a hook to this script
        _call("git init --quiet --bare " + app, cwd=GIT_ROOT, shell=True)
        with open(hook_path, 'w') as h:
            h.write("""#!/usr/bin/env bash
set -e; set -o pipefail;
cat | KOKA_ROOT="{KOKA_ROOT:s}" {KOKA_CMD:s} git-hook {app:s}""".format(**env))
        # Make the hook executable by our user
        os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IXUSR)
    # Handle the actual receive. We'll be called with 'git-hook' after it happens
    #_call('git-shell -c "{}" '.format(argv[1] + " '{}'".format(app)), cwd=GIT_ROOT, shell=True)


def git_upload_pack(app):
    """INTERNAL: Handle git upload pack for an app"""

    env = globals()
    env.update(locals())
    # Handle the actual receive. We'll be called with 'git-hook' after it happens
    #_call('git-shell -c "{}" '.format(argv[1] + " '{}'".format(app)), cwd=GIT_ROOT, shell=True)


def main():
    _argvs = sys.argv
    script_name = sys.argv[0].split('/')[-1]

    # Internal GIT command
    if _argvs and len(_argvs) >= 3 and _argvs[1] in ["git-hook", "git-upload-pack", "git-receive-pack"]:
        cmd = sys.argv[1]
        app = sys.argv[2]
        if cmd == "git-hook":
            git_hook(app)
        elif cmd == "git-upload-pack":
            git_upload_pack(app)
        elif cmd == "git-receive-pack":
            git_receive_pack(app)
    else:
        cli()
