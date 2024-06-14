import time
from flaskr import app
from flask import Blueprint, request, session, url_for
from flask import render_template, redirect, jsonify, make_response
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from .models import db, User, OAuth2Client
from .oidc.oauth2 import authorization, require_oauth, user_info_api

from .appActions.auth_decorator import login_required, system_admin_required

IDP_DOMAIN = app.config['ife_IDP_DOMAIN']

bp_oidc = Blueprint('oidc', __name__, template_folder='templates')


def current_user():
    if 'id' in session:
        user = User.query.filter_by(mattermost_id=session['id']).first()
        if not user:
            raise Exception("current_user unable to locate user")  
        return User.query.filter_by(mattermost_id=session['id']).first()
    return None


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]

@bp_oidc.route("/", methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_home():
    clients = OAuth2Client.query.all()
    return render_template('oidc_list.html', clients=clients, show_internal_banner=True)

@bp_oidc.route('/create_client', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_create_client():
    return render_template('oidc_create_client.html', show_internal_banner=True)

@bp_oidc.route('/create_client', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_create_client():
    from .appActions import user_manager
    local_id = user_manager.get_local_id(session['id'])

    form = request.form
    client_id = gen_salt(24)
    client = OAuth2Client(client_id=client_id, user_id=local_id)
    # Mixin doesn't set the issue_at date
    client.client_id_issued_at = int(time.time())
    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    db.session.add(client)
    db.session.commit()
    return redirect(url_for("oidc.get_home"))

@bp_oidc.route('/delete_client', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_delete_client():
    form = request.form
    client_id = form['client_id']
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for("oidc.get_home"))


@bp_oidc.route('/oauth/authorize', methods=['GET'], host=IDP_DOMAIN)
@login_required
def get_authorize():
    from .appActions import user_manager
    local_id = user_manager.get_local_id(session['id'])
    
    try:
        grant = authorization.get_consent_grant(end_user=local_id)
        client = grant.client
        scope = client.get_allowed_scope(grant.request.scope)
    except OAuth2Error as error:
        return jsonify(dict(error.get_body()))
    return render_template('oidc_authorize.html', user=session['id'], grant=grant, show_internal_banner=True)


@bp_oidc.route('/oauth/authorize', methods=['POST'], host=IDP_DOMAIN)
@login_required
def post_authorize():
    if "confirm" in dict(request.form).keys():
        grant_user = current_user()
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)

@bp_oidc.route('/oauth/token', methods=['POST'], host=IDP_DOMAIN)
def issue_token():
    return authorization.create_token_response()


@bp_oidc.route('/oauth/userinfo', host=IDP_DOMAIN)
@require_oauth('profile')
def api_me():
    user_info = user_info_api(current_token.user, current_token.scope)

    if not user_info:
        return make_response("500 - No matching user", 500)

    return jsonify(user_info)