# Only Local Auth routes 
# for OAuth2 endpoints as client

from flask import Blueprint, render_template, session, request, url_for, redirect, make_response
from authlib.integrations.flask_client import OAuth

from flaskr import app
from .appActions import appConfig


IDP_DOMAIN = app.config['ife_IDP_DOMAIN']
ife_MATTERMOST_URL = app.config['ife_MATTERMOST_URL']
UPSTREAM_COOKIE = app.config['ife_UPSTREAM_COOKIE']

local_auth = Blueprint('local_auth', __name__, template_folder='templates')


oauth_IFE = OAuth(app)
mattermost_IFE = oauth_IFE.register(
    name='mattermost_IFE',
    client_id=appConfig.get_oauth_client_id(),
    client_secret=appConfig.get_oauth_client_secret(),
    access_token_url= ife_MATTERMOST_URL + '/oauth/access_token',
    access_token_params=None,
    authorize_url= ife_MATTERMOST_URL + '/oauth/authorize',
    authorize_params=None,
    api_base_url= ife_MATTERMOST_URL + '/api/v4/',
    userinfo_endpoint= ife_MATTERMOST_URL + '/api/v4/users/me',
    client_kwargs = {
    'token_endpoint_auth_method': 'client_secret_post',} # Mattermost requires post
)

@local_auth.route('/login', methods=['GET'], host=IDP_DOMAIN)
def auth_providers_get():
    service_uri = request.args.get("service_uri", "")
    if len(service_uri) > 5:
        import urllib.parse
        service_uri = urllib.parse.quote_plus(service_uri)

    # If cookie has been set, redirect to Mattermost 
    # for when IdP session has expired but user has been logged in and is typically already logged into Mattermost
    if request.cookies.get("IFE_MM_USERNAME", None) != None:
        return redirect(url_for('local_auth.ife_login_mattermost', service_uri=service_uri))
    
    return render_template('auth-providers.html', service_uri=service_uri)

@local_auth.route('/login/oauth2/mattermost/generic', methods=['GET'], host=IDP_DOMAIN)
def ife_login_mattermost():
    redirect_uri = url_for('local_auth.authorize_mattermost', _external=True)
    service_uri = request.args.get("service_uri", "")
    if (len(service_uri) > 5):
        # If service_uri specified 
        # Set cookie to allow redirect to originating page
        try:
            import urllib.parse

            service_uri = urllib.parse.unquote_plus(service_uri)

            response = make_response(redirect(url_for('local_auth.ife_login_mattermost', _external=True)))
            response.set_cookie(key="IFE_post_sso_destination", max_age=180, value=service_uri, secure=True, httponly=True, samesite='Lax')
            return response

        except Exception as e:
            app.logger.error("router - ife_login_mattermost - custom uri failed - " + str(e))

        
    return mattermost_IFE.authorize_redirect(redirect_uri)

@local_auth.route('/authorize/oauth2/mattermost/generic', host=IDP_DOMAIN)
def authorize_mattermost():

    # Pull token from auth request
    from authlib.integrations.base_client import MismatchingStateError, MissingRequestTokenError, MissingTokenError
    try:
        token = mattermost_IFE.authorize_access_token()  # Access token from mattermost (needed to get user info)
    except MismatchingStateError:
        message = "CSRF Warning, please contact your administrator. <br>[Code: MismatchingStateError]"
        return render_template('index.html', error_section=message), 500
    except MissingRequestTokenError:
        message = "CSRF Warning, please contact your administrator. <br>[Code: MissingRequestTokenError]"
        return render_template('index.html', error_section=message), 500
    except MissingTokenError:
        message = "CSRF Warning, please contact your administrator. <br>[Code: MissingTokenError]"
        return render_template('index.html', error_section=message), 500

    except Exception as e:
        message = "There has been an authentication error, please contact your administrator. <br>[Code: authorize_access_token Exception]"
        app.logger.error("router - authorize_mattermost - user_manager class handle_login failed - authorize_access_token Exception " + str(e))
        return render_template('index.html', error_section=message), 500

    # Check if token is present (can be missing if misconfigured)
    if 'access_token' not in token:
        message = "There has been an authentication error, please contact your administrator. <br>[Code: OAuth2 Token Invalid]"
        return render_template('index.html', error_section=message), 500

    # Get user data from Mattermost with access token
    try:
        resp = oauth_IFE.mattermost_IFE.get('users/me', token=token) # Request user data
        user_info = resp.json()
    except Exception as e:
        for key in list(session.keys()):
            session.pop(key)
        message = "There has been an authentication error, please contact your administrator. <br>[Code: OAuth2 user info error]"
        app.logger.error("router - authorize_mattermost - OAuth2 get user attributes failed " + str(e))
        return render_template('index.html', error_section=message), 500

    # Convert user JSON to session info
    try:
        session['id'] = user_info['id']
        session['username'] = user_info['username']
        session['email'] = user_info['email']
        session['email_verified'] = user_info['email_verified']
        session['first_name'] = str(user_info['first_name']).strip()
        session['last_name'] = str(user_info['last_name']).strip()
        session['roles'] = user_info.get('roles', "")
        session['mfa_active'] = user_info.get('mfa_active', "")
        session['nickname'] = user_info.get('nickname', "")
        session['create_at'] = user_info.get('create_at', "")
    except:
        for key in list(session.keys()):
            session.pop(key)
        message = "There has been an authentication error, please contact your administrator. <br>[Code: Unable to convert session]"
        app.logger.error("router - authorize_mattermost - convert user attributes")
        return render_template('index.html', error_section=message), 500 

    # Flag no first and last name
    if len(session['first_name']) < 1 or len(session['last_name']) < 1:
        for key in list(session.keys()):
            session.pop(key)
        message = "Invalid attributes. Please set your first and last name, and try again."
        return render_template('index.html', error_section=message), 500 


    # Pull additional data for logged in user
    try:
        from .appActions import user_manager, ife_sso_token
        user_local_data = user_manager.handle_login(user_info)
    except Exception as e:
        for key in list(session.keys()):
            session.pop(key)
        message = "There has been an authentication error, please contact your administrator. <br>[Code: handle_login Exception]"
        app.logger.error("router - authorize_mattermost - user_manager class handle_login failed - " + str(e))
        return render_template('index.html', error_section=message), 500
        
    if user_local_data['preferred_username'] == False:
        for key in list(session.keys()):
            session.pop(key)
        message = "There has been an authentication error, please contact your administrator. <br>[Code: user_local_data " + user_local_data['error'] + "]"
        return render_template('index.html', error_section=message), 500

    # Add token to portal session to allow remote revocation 
    sso_token = ife_sso_token.new_domain_sso(user_info['id'], request.headers)
    if sso_token == False:
        app.logger.error("router - authorize_mattermost - global_sso new session failure")
    else:
        session['IFE_SSO'] = sso_token

    # When something goes wrong with getting permissions
    # or adding new user to DB
    if sso_token == False:
        for key in list(session.keys()):
            session.pop(key)
        message = "There has been an authentication error, please contact your administrator. <br>[Code: global_sso]"
        return render_template('index.html', error_section=message), 500


    # Set preferred_username in JWT format
    session['preferred_username'] = user_local_data['preferred_username']


    # Send user back to where they originally received a request to sign in (to very specific page)
    # Check if post-sso cookie is available
    # if available, check if valid then redirect user while destroying cookie
    response = make_response(redirect("/"))
    try:
        import urllib.parse
        from urllib.parse import urlparse
        service_uri = request.cookies.get('IFE_post_sso_destination', "")
        service_uri = urllib.parse.unquote_plus(service_uri)
        service_domain = urlparse(service_uri).hostname
        service_scheme = urlparse(service_uri).scheme

        redirect_okay = False

        if (len(service_uri) > 2) and (service_scheme == "https") and (service_domain.endswith(app.config['ife_TRUSTED_ROOT'])):
            redirect_okay = True

        if redirect_okay:
            response = make_response(redirect(service_uri))
    except Exception as e:
        app.logger.error("router - authorize_mattermost - referrer_url handler failed - " + str(e))

    response.delete_cookie('IFE_post_sso_destination')
    response.set_cookie(key="IFE_GLOBAL_SSO_CRED", value=sso_token, domain=app.config['ife_GLOBAL_SSO_DOMAIN'], secure=True, httponly=True, samesite='Lax')
    response.set_cookie(key="IFE_MM_USERNAME", value=session['username'], domain=app.config['ife_GLOBAL_SSO_DOMAIN'], secure=True, httponly=False, samesite='Lax')
    response.set_cookie(key="IFE_GIVEN_NAME", value=session['first_name'], domain=app.config['ife_GLOBAL_SSO_DOMAIN'], secure=True, httponly=False, samesite='Lax')
    return response

@local_auth.route('/logout', host=IDP_DOMAIN)
def logout():
    from .appActions import ife_sso_token

    IFE_GLOBAL_SSO_CRED = request.cookies.get('IFE_GLOBAL_SSO_CRED', "")

    # If Authentik session exists, redirect to URL logout
    upstream_cookie_set = request.cookies.get(UPSTREAM_COOKIE, False)
    if upstream_cookie_set != False:
        return redirect(app.config['ife_UPSTREAM_SSO_DOMAIN'] + app.config['ife_UPSTREAM_SSO_PATH'])
    
    for key in list(session.keys()):
        session.pop(key)

    ife_sso_token.handle_revoke_current_session(IFE_GLOBAL_SSO_CRED)

    response =  make_response(render_template('logout.html', show_internal_banner="Blank"))    

    for cookie in request.cookies:
        response.delete_cookie(key=cookie, domain=app.config['ife_GLOBAL_SSO_DOMAIN'])

    return response
