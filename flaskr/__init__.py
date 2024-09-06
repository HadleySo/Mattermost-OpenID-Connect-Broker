from flask import Flask
import os, configparser
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))
fullConfigPath = os.path.abspath(os.path.join(basedir, '../idp.cfg'))

cfg = configparser.ConfigParser()
cfg.read(fullConfigPath)


# create the app
app = Flask(__name__, host_matching=True, static_host=cfg.get('DOMAINS', 'idp_domain'))

app.config['app_version'] = "2.4.0"
app.config['ife_IDP_DOMAIN'] = cfg.get('DOMAINS', 'idp_domain')
app.config['ife_UPSTREAM_SSO_DOMAIN'] = cfg.get('DOMAINS', 'upstream_sso_domain')
app.config['ife_UPSTREAM_COOKIE'] = cfg.get('DOMAINS', 'upstream_cookie')
app.config['ife_UPSTREAM_SSO_PATH'] = cfg.get('DOMAINS', 'upstream_sso_path')

app.config['ife_IDP_PROTOCOL'] = "https://"
app.config['ife_GLOBAL_SSO_DOMAIN'] = cfg.get('DOMAINS', 'sso_domain')
app.config['ife_MATTERMOST_URL'] = cfg.get('DOMAINS', 'mattermost_url')
app.config['ife_TRUSTED_ROOT'] = cfg.get('DOMAINS', 'trusted_root')

app.config['ife_EMAIL_SENDER_NAME'] = cfg.get('SMTP', 'sender_name')
app.config['ife_EMAIL_SENDER_ADDRESS'] = cfg.get('SMTP', 'sender_address')

app.config['ife_EMAIL_SERVER'] = cfg.get('SMTP', 'server')
app.config['ife_EMAIL_PORT'] = cfg.get('SMTP', 'port')
app.config['ife_EMAIL_TLS'] = cfg.get('SMTP', 'tls')



# SQALCHMY Database for OIDC
odic_db = cfg.get('DATABASE', 'path')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"{odic_db}"

# Register other routes
from . import router_localAuth, router_jwt, router_admin, router_oidc, router_functions, router_api01
app.register_blueprint(router_localAuth.local_auth)
app.register_blueprint(router_api01.route_api_01, url_prefix = "/api/v1")
app.register_blueprint(router_jwt.local_jwt, url_prefix = "/api/v1/idp/jwt")
app.register_blueprint(router_admin.router_admin, url_prefix = "/admin")
app.register_blueprint(router_oidc.bp_oidc, url_prefix = "/oidc")
app.register_blueprint(router_functions.router_functions)


from flaskr import router


# Link SQALCHMY
from .models import db
from .oidc.oauth2 import config_oauth
db.init_app(app)
config_oauth(app)

migrate = Migrate(app, db)
