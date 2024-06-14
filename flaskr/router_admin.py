# Only routes for Admin

from flask import Blueprint, session, render_template, request, url_for, redirect

from flaskr import app

from .appActions.auth_decorator import login_required, system_admin_required

IDP_DOMAIN = app.config['ife_IDP_DOMAIN']


router_admin = Blueprint('router_admin', __name__, template_folder='templates')


@app.template_filter('ctime')
def timectime(s):
    import time
    return time.ctime(s) # datetime.datetime.fromtimestamp(s)

@router_admin.route('/', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def admin_get_home():
    return render_template("admin_index.html", show_internal_banner=True)

@router_admin.route('/list-domains', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_domains():
    from .appActions import domain_manager

    domainData = domain_manager.list_all()

    return render_template("domain_list.html", domainData=domainData, show_internal_banner=True)

@router_admin.route('/add-domain', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_add_domain():
    return render_template("domain_add.html", show_internal_banner=True)


@router_admin.route('/add-domain', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_add_domain():
    from .appActions import domain_manager
    
    result = domain_manager.add(**request.form)

    if result == True:
        return redirect(url_for("router_admin.get_domains"))
    
    message = "Error adding domain"
    return render_template('index.html', error_section=message), 500

@router_admin.route('/list-all', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_list_all():
    from .appActions import user_manager

    userData = user_manager.list_all()

    return render_template("admin_list.html", userData=userData, show_internal_banner=True)

@router_admin.route('/list-sessions', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_list_sessions():
    from .appActions import session_manager
    import time

    since_epoch = int(time.time())

    before_date = request.args.get('before_date', since_epoch)
    if type(before_date) == str:
        if len(before_date) < 11:
            import datetime
            before_date = before_date.split("-")
            before_date = datetime.datetime(int(before_date[0]), int(before_date[1]), int(before_date[2])).timestamp()


    data = session_manager.list_all(before_date)

    return render_template("session_list.html", data=data, show_internal_banner=True)

@router_admin.route('/list-sessions/', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_list_sessions_user():
    mattermost_id = request.form.get("user","")
    return redirect(url_for("router_admin.get_list_sessions_user", mattermost_id=mattermost_id))

@router_admin.route('/list-sessions/<mattermost_id>', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_list_sessions_user(mattermost_id):
    from .appActions import session_manager
    import time

    since_epoch = int(time.time())

    before_date = request.args.get('before_date', since_epoch)
    data = session_manager.list_mine(mattermost_id, before_date)

    return render_template("session_list.html", data=data, show_internal_banner=True)

@router_admin.route('/user-info/', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_user_info():
    mattermost_id = request.form.get("user","")
    return redirect(url_for("router_admin.get_user_info", mattermost_id=mattermost_id))

@router_admin.route('/user-info/<mattermost_id>', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_user_info(mattermost_id):
    from .appActions import user_manager

    data = user_manager.get_admin_user_data(mattermost_id)

    return render_template("admin_user_info.html", data=data, show_internal_banner=True)

@router_admin.route('/load-edit-form/', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_load_edit_form():
    mattermost_id = request.form.get("user","")
    return redirect(url_for("router_admin.get_user_edit", mattermost_id=mattermost_id))

@router_admin.route('/edit-user/<mattermost_id>', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_user_edit(mattermost_id):
    from .appActions import user_manager

    data = user_manager.get_admin_user_data(mattermost_id)

    return render_template("admin_user_edit.html", data=data, show_internal_banner=True)

@router_admin.route('/edit-user/<mattermost_id>', methods=['POST'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def post_user_edit(mattermost_id):
    from .appActions import user_manager

    if mattermost_id != request.form.get("id", ""):
        return render_template('index.html', error_section="Mattermost ID mismatch"), 400 

    result = user_manager.modify_user_display(request.form)

    if result:
        return redirect(url_for("router_admin.admin_get_home"))

    return render_template('index.html', error_section="Error processing request"), 500 
