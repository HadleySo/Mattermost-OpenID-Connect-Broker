from flask import session, redirect, render_template
from functools import wraps


def login_required(f):
    """Require an active session.   

    Checks for:
    1. User ID in session
    2. Boolean true for email_verified
    3. Valid SSO token (not revoked)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email_verified = dict(session).get('email_verified', None)
        token_cookie = dict(session).get('IFE_SSO', "")


        # Put imports under failure cases to avoid running imports on every web request
        # since most requests will not encounter failure cases / are logged in
        
        if 'id' not in dict(session):
            from flask import request
            import urllib.parse
            redirect_target = "/login?service_uri=" + urllib.parse.quote_plus(request.url)
            return redirect(redirect_target)
        if (not email_verified == True):
            from flask import request
            import urllib.parse
            redirect_target = "/login?service_uri=" + urllib.parse.quote_plus(request.url)
            return redirect(redirect_target)

        # Allow for remote revocation
        from . import ife_sso_token
        result = ife_sso_token.validate_domain_session(token_cookie)
        if result['result'] != True:
            from flask import request
            import urllib.parse
            redirect_target = "/login?service_uri=" + urllib.parse.quote_plus(request.url)
            return redirect(redirect_target)

        return f(*args, **kwargs)
        

    return decorated_function
    
def mfa_required(f):
    """Require MFA enabled, does not check if MFA was validated. 
    If MFA is not present will render index page with instructions.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        mfa_active = dict(session).get('mfa_active', None)

        if not mfa_active == True:
            error = '''MFA must be enabled to access this resource. <br><br>
            Configure in Mattermost desktop:
            <ol>
                <li>
                    Download a MFA app like DUO or Google Authenticator
                </li>
                <li>
                    From your profile picture, select Profile > Security
                </li>
                <li>
                    Under Multi-factor Authentication, select Edit
                </li>
            </ol>
            Contact your administrator for assistance.
            '''
            return render_template('index.html', error_section=error, show_internal_banner=True), 401

        return f(*args, **kwargs)
        

    return decorated_function

def system_admin_required(f):
    """Require Mattermost system admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        roles = dict(session).get('roles', None)

        if 'system_admin' not in roles:
            return render_template('index.html', error="You lack elevated privileges. Contact your administrator.", show_internal_banner=True), 403

        return f(*args, **kwargs)
        

    return decorated_function
    
