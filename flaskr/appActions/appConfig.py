import configparser, os


basedir = os.path.abspath(os.path.dirname(__file__))
fullConfigPath = os.path.abspath(os.path.join(basedir, '../../idp.cfg'))

# SMTP
def get_mail_username():
    """Fetch and return AWS SES SMTP Username.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('SMTP', 'username')

def get_mail_password():
    """Fetch and return AWS SES SMTP Password.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('SMTP', 'password')


# OAUTH2
def get_oauth_client_id():
    """Fetch and return Mattermost OAuth2 Client ID.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('OAUTH', 'client_id')

def get_oauth_client_secret():
    """Fetch and return Mattermost OAuth2 Client Secret.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('OAUTH', 'client_secret')


# APP SETTINGS
def get_flask_session_secret_key():
    """Fetch and return flask session key.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('APP_LOCAL', 'app_secret_key')

def get_domain_sso_secret_key():
    """Fetch and return domain SSO key.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('APP_LOCAL', 'sso_domain_key')

# JWT
def get_jwt_private_path():
    """Get location of public key
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('JWT', 'private_key') 

def get_jwt_public_path():
    """Get location of public key
    """
    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)
    return cfg.get('JWT', 'public_key') 

# MISC
def handle_revoke_portal_sessions():
    """Changes URL salt for Portal sessions. Revokes all portal sessions.
    """
    import secrets
    new_salt = secrets.token_urlsafe()

    cfg = configparser.ConfigParser()
    cfg.read(fullConfigPath)

    cfg.set('URL_SERIALIZER', 'security_password_salt', new_salt)

    with open(fullConfigPath, 'w') as saveConfig:
        cfg.write(saveConfig)
