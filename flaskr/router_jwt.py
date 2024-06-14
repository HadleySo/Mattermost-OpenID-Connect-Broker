# Only routes for JWT

from flask import Blueprint,request, redirect, session

from flaskr import app
from .appActions import appConfig

from .appActions.auth_decorator import login_required

IDP_DOMAIN = app.config['ife_IDP_DOMAIN']


local_jwt = Blueprint('local_jwt', __name__, template_folder='templates')


@local_jwt.route('/request', methods=['GET'], host=IDP_DOMAIN)
@login_required
def api_vi_idp_jwt_request():
    from authlib.jose import jwt
    import time, uuid

    auth_url = request.args.get("auth_url", "")
    since_epoch = int(time.time())

    if len(auth_url) < 5:
        return ('400 Bad request', 400)


    if app.config['ife_IDP_DOMAIN'] in auth_url:
        return ('400 Bad request', 400)

    # Must put exp, nbf, iat in seconds according to RFC7519 Section 2

    header = {'alg': 'RS256'}
    payload = {
        'iss': app.config['ife_IDP_DOMAIN'], 
        'sub': str(session['id']),
        'aud': auth_url,
        'exp': since_epoch+15,
        'nbf': since_epoch,
        'iat': since_epoch,
        'jti': str(uuid.uuid4()),
        'given_name': session['first_name'],
        'family_name': session['last_name'],
        'nickname': session['nickname'],
        'email': session['email'],
        'email_verified': session['email_verified'],
        'roles': session['roles'],
        'preferred_username': session['preferred_username']}

    with open(appConfig.get_jwt_private_path()) as private_key:
        private_key_content = private_key.read()

    jtw_encoded = jwt.encode(header, payload, private_key_content).decode("utf-8") 

    return redirect(auth_url + jtw_encoded)


@local_jwt.route('/public_key', methods=['GET'], host=IDP_DOMAIN)
def api_vi_idp_jwt_public_key():
    from flask import send_file

    return send_file(appConfig.get_jwt_public_path())