from flask import Blueprint,request, redirect, session, render_template

from flaskr import app
from .appActions import appConfig

from .appActions.auth_decorator import login_required, system_admin_required

router_functions = Blueprint('router_functions', __name__, template_folder='templates')

IDP_DOMAIN = app.config['ife_IDP_DOMAIN']


@app.template_filter('joindate')
def tijoindatemectime(s):
    from datetime import datetime
    return datetime.fromtimestamp(s/1000).strftime(' %d %B %Y')

@router_functions.route('/my-sessions', methods=['GET'], host=IDP_DOMAIN)
@login_required
def get_my_sessions():
    from .appActions import session_manager
    import time

    since_epoch = int(time.time())

    before_date = request.args.get('before_date', since_epoch)

    if type(before_date) == str:
        if len(before_date) < 11:
            import datetime
            before_date = before_date.split("-")
            before_date = datetime.datetime(int(before_date[0]), int(before_date[1]), int(before_date[2])).timestamp()

    data = session_manager.list_mine(session['id'], before_date)

    return render_template("session_list.html", data=data, show_internal_banner=True)


@router_functions.route('/my-info', methods=['GET'], host=IDP_DOMAIN)
@login_required
def get_my_info():
    from .appActions import user_manager

    data = user_manager.get_oidc(session['id'])

    return render_template("user_info.html", data=data, show_internal_banner=True)




@router_functions.route('/session/<session_id>', methods=['GET'], host=IDP_DOMAIN)
@login_required
def get_session(session_id):
    from .appActions import session_manager

    data = session_manager.list_session(session_id=session_id, session=session)

    return render_template("session_detail.html", data=data, show_internal_banner=True)


@router_functions.route('/revoke-session', methods=['POST'], host=IDP_DOMAIN)
@login_required
def post_revoke():
    from .appActions import session_manager
    formData = request.form

    result = session_manager.revoke(formData['session_id'], session)

    if result:
        return redirect("/")
    
    message = "Unable to complete request"
    return render_template('index.html', error_section=message, show_internal_banner=True)
