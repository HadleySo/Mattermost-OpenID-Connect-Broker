from .. import models
from sqlalchemy import select, update

def search_user_given(query: str, limit: int = 15):
    """Run a case sensitive search for users, return JSON of ID and Name.
    :param query: Search Query
    :limit query: Max records to return, default 15
    """

    results = models.db.session.query(models.User).filter(models.User.first_name.startswith(query)).limit(limit).all()

    result_list = []
    for user in results:
        result_list.append(
            {'id': user.mattermost_id, 'text': user.first_name + " " + user.last_name}
            )
        
    result = {'results': result_list, "pagination": {"more": False}}

    return result

def search_email_given(query: str, limit: int = 15):
    """Run a case sensitive search for users, return JSON of ID and Name.
    :param query: Search Query
    :limit query: Max records to return, default 15
    """

    results = models.db.session.query(models.User).filter(models.User.email.startswith(query)).limit(limit).all()

    result_list = []
    for user in results:
        result_list.append(
            {'id': user.mattermost_id, 'text': user.first_name + " " + user.last_name}
            )
        
    result = {'results': result_list, "pagination": {"more": False}}

    return result