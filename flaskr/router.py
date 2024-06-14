import logging
from flask import render_template, request, redirect, url_for, session, make_response
from flask_cors import CORS

from authlib.integrations.flask_oauth2.errors import _HTTPException
from werkzeug.exceptions import MethodNotAllowed

from authlib.jose import jwt

from datetime import timedelta
from flaskr import app

from .appActions import appConfig

logging.basicConfig(filename='error.log', level=logging.ERROR, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

IDP_PROTOCOL = app.config['ife_IDP_PROTOCOL'] 
IDP_DOMAIN = app.config['ife_IDP_DOMAIN'] 
GLOBAL_SSO_DOMAIN = app.config['ife_GLOBAL_SSO_DOMAIN'] 
CORS(app, origins=[IDP_PROTOCOL + IDP_DOMAIN])


# Decorator for routes that should be accessible only by logged in users
from .appActions.auth_decorator import login_required, system_admin_required

# Session and OAuth config
app.secret_key = appConfig.get_flask_session_secret_key()
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_NAME='IFE_IdP_local_session',
    MAIL_SERVER=app.config['ife_EMAIL_SERVER'],
    MAIL_PORT=app.config['ife_EMAIL_PORT'],
    MAIL_USE_TLS=app.config['ife_EMAIL_TLS'],
    MAIL_DEFAULT_SENDER=(app.config['ife_EMAIL_SENDER_NAME'], app.config['ife_EMAIL_SENDER_ADDRESS']),
    MAIL_USERNAME=appConfig.get_mail_username(),
    MAIL_PASSWORD=appConfig.get_mail_password(),
)
ife_MATTERMOST_URL = app.config['ife_MATTERMOST_URL']

@app.context_processor
def inject_template_globals():
    # inject timestamp and dynamic variables in every page
    from datetime import datetime
    stamp = datetime.utcnow()
    timeStamp =  str(stamp) + " UTC"
    return {
        'timeStamp': timeStamp,
        'CF_RAY_id': request.headers.get('CF-RAY', "-"),
        'CF_ip_country': request.headers.get('CF-IPCountry', "-"),
        'portal_app_version': app.config['app_version'] ,
        'ife_MATTERMOST_URL': app.config['ife_MATTERMOST_URL'],
        'ife_AUTHENTIK_DOMAIN' : app.config['ife_AUTHENTIK_DOMAIN'],
        'date_utc_now': datetime.utcnow()
    }

@app.before_request
def before_request():
    # Set session timeout on inactivity
    # Session cookie for Portal app
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    session.modified = True



@app.route('/localAuth/user/revoke-sessions', methods=['GET'], host=IDP_DOMAIN)
@login_required
def sso_revoke_user_sessions():
    from .appActions import ife_sso_token
    ife_sso_token.revoke_user_all_sessions(session['id'])

    for key in list(session.keys()):
        session.pop(key)
    
    message = 'Revoked all IdP sessions. Revoke all <a href="' + ife_MATTERMOST_URL + '">Mattermost</a> \
        sessions to finish revoking sessions.'
    response =  make_response(render_template('index.html', message=message))
    response.delete_cookie(key="IFE_GLOBAL_SSO_CRED", domain=GLOBAL_SSO_DOMAIN)
    return response


# 
# HOME PAGE
# 
@app.route('/', methods=['GET'], host=IDP_DOMAIN)
@login_required
def root_get():
    from datetime import datetime

    roles = dict(session).get('roles', None)
    if 'system_admin' in roles:
        is_admin = True
    else:
        is_admin = False
        
    return render_template("home.html", show_internal_banner=True, \
        first_name=session['first_name'], is_admin=is_admin)


# Check if logged in
@app.route('/api/v1/idp/check/membership', methods=['GET'], host=IDP_DOMAIN)
def api_v1_idp_check_membership():
    from .appActions import ife_sso_token
    token_cookie = request.cookies.get('IFE_GLOBAL_SSO_CRED', "")

    if len(token_cookie) < 2:
        return ('401 Unauthorized -  No SSO token', 401)

    token_validation_result = ife_sso_token.validate_domain_session(token_cookie)

    if token_validation_result['result'] == True:
        return ('204 - Success without content', 204)
    elif token_validation_result['result'] == False:
        return ('403 Forbidden - Client identity known', 403)

    return ('400 Bad request', 400)


# Will always return 200
# Header will be set based on SSO cookie
@app.route('/api/v1/idp/check/mediawiki', methods=['GET'], host=IDP_DOMAIN)
def api_v1_idp_check_mediawiki():
    from .appActions import ife_sso_token, user_manager
    token_cookie = request.cookies.get('IFE_GLOBAL_SSO_CRED', "")

    if len(token_cookie) < 2:
        # if no cookie, return ok with blank header
        response = make_response('204 - Success without content', 204)
        response.headers['X-IFE-SSO-NETID'] = ""
        return response

    token_validation_result = ife_sso_token.validate_domain_session(token_cookie)

    if token_validation_result['result'] == False:
        # cookie exists but is not valid
        response = make_response('204 - Success without content', 204)
        response.headers['X-IFE-SSO-NETID'] = ""
        return response


    # Session does not exist, must use token_validation_result
    netID =  user_manager.get_preferred_username(token_validation_result['user_id'])

    response = make_response('200 - Ok', 200)
    response.headers['X-IFE-SSO-NETID'] = netID
    return response

# Header will be set based on SSO cookie
@app.route('/api/v1/idp/check/passthrough_strict', methods=['GET'], host=IDP_DOMAIN)
def api_v1_idp_check_passthrough_strict():
    from .appActions import ife_sso_token, user_manager
    token_cookie = request.cookies.get('IFE_GLOBAL_SSO_CRED', "")

    if len(token_cookie) < 2:
        # if no cookie, return 401 with blank header
        response = make_response('401 Forbidden - Client identity unknown', 401)
        response.headers['X-IFE-SSO-NETID'] = ""
        return response

    token_validation_result = ife_sso_token.validate_domain_session(token_cookie)

    if token_validation_result['result'] == False:
        # cookie exists but is not valid
        response = make_response('403 Forbidden - Client identity known', 403)
        response.headers['X-IFE-SSO-NETID'] = ""
        return response


    # Session does not exist, must use token_validation_result
    netID =  user_manager.get_preferred_username(token_validation_result['user_id'])

    response = make_response('200 - Ok', 200)
    response.headers['X-IFE-SSO-NETID'] = netID
    return response

@app.route('/api/v1/preferred_username/<email>', methods=['GET'], host=IDP_DOMAIN)
def api_v1_get_preferred_username(email:str):
    from .appActions import usernameMapper

    result = usernameMapper.username_from_domain(email)
    if result == False:
        return "Bad request", 400
    
    return {"preferred_username": result}

@app.route('/.well-known/openid-configuration', methods=['GET'], host=IDP_DOMAIN)
def well_known():
    wk_json = {
        "issuer": app.config['ife_IDP_DOMAIN'], 
        "authorization_endpoint": url_for('oidc.get_authorize',  _external=True),
        "token_endpoint": url_for('oidc.issue_token',  _external=True),
        "userinfo_endpoint": url_for('oidc.api_me',  _external=True),
        "jwks_uri": url_for('local_jwt.api_vi_idp_jwt_public_key',  _external=True),
        "scopes_supported": ['openid', 'profile'],
        "response_types_supported" : ['code'],
        "token_endpoint_auth_methods_supported" : ['client_secret_basic', 'client_secret_post', 'none'],
        "id_token_signing_alg_values_supported" : ['RS256']
    }

    return wk_json

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
@app.errorhandler(MethodNotAllowed)
def method_error(e):
    return make_response("405", 405)
@app.errorhandler(_HTTPException)
def oauth2_auth_error(e):
    return e
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error("router - global exception catcher app.errorhandler - " + str(e) + str(type(e)))
    return render_template('500.html'), 500
