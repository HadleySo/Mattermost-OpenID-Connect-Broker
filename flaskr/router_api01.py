from flask import render_template, Blueprint, session, request

from .appActions.auth_decorator import login_required, system_admin_required
from flaskr import app

route_api_01 = Blueprint('route_api_01', __name__, template_folder='templates')
IDP_DOMAIN = app.config['ife_IDP_DOMAIN']


@route_api_01.route('/admin/users/search', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_all():
    """JSON of userid and names"""

    args = request.args

    term = args.get("term", "")
    if len(term) < 1:
        return "Query too short", 400
    
    from .appActions import api_01
    results = api_01.search_user_given(term)


    return results


@route_api_01.route('/admin/email/search', methods=['GET'], host=IDP_DOMAIN)
@login_required
@system_admin_required
def get_email():
    """JSON of userid and names"""

    args = request.args

    term = args.get("term", "")
    if len(term) < 1:
        return "Query too short", 400
    
    from .appActions import api_01
    results = api_01.search_email_given(term)


    return results