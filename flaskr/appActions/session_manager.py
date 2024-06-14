from .. import models
from sqlalchemy import update, desc


def revoke(session_id: str, session):
    """Revokes a given session based on Session ID. User must be session owner or admin

    :param session_id: Requested session to revoke
    :param session: Flask session data
    """

    user_allowed = False

    # Check if system admin
    if 'system_admin' in session['roles'].split(" "):
        user_allowed = True

    # Get Mattermost ID of session
    session_mattermost_id = models.db.session.query(models.SessionTokens.mattermost_id).filter(models.SessionTokens.session_id == session_id).first()
    
    # If Session Mattermost ID is same as Requestor Mattermost ID
    if session_mattermost_id[0] == session['id']:
        user_allowed = True

    if user_allowed:
        stmt_01 = (update(models.SessionTokens).where(models.SessionTokens.session_id == session_id)\
               .values({"valid": False}))
        models.db.session.execute(stmt_01)
        models.db.session.commit()

        return True
    return False

def list_session(session_id: str, session):
    """List a specific session, will check if user allowed
    Formatted in list of JSON

    :param session_id: Session ID
    :param session: Flask session data
    """

    user_allowed = False

    # Check if system admin
    if 'system_admin' in session['roles'].split(" "):
        user_allowed = True

    # Get Mattermost ID of session
    session_mattermost_id = models.db.session.query(models.SessionTokens.mattermost_id).filter(models.SessionTokens.session_id == session_id).first()
    
    # If Session Mattermost ID is same as Requestor Mattermost ID
    if session_mattermost_id[0] == session['id']:
        user_allowed = True

    if user_allowed:
        orm_result = models.db.session.query(models.SessionTokens, models.User).filter(models.SessionTokens.session_id == session_id)\
                .join(models.User, models.SessionTokens.mattermost_id == models.User.mattermost_id)\
                    .order_by(desc(models.SessionTokens.created_timedate)).all()

        return orm_result
    return []
    

def list_mine(mattermost_id: str, before_date: int):
    """List a given user's sessions based on Mattermost ID
    Formatted in list of JSON

    :param mattermost_id: User's Mattermost ID
    """

    orm_result = models.db.session.query(models.SessionTokens, models.User).filter(models.SessionTokens.mattermost_id == mattermost_id)\
        .join(models.User, models.SessionTokens.mattermost_id == models.User.mattermost_id)\
            .where(models.SessionTokens.created_timedate <= before_date)\
            .order_by(desc(models.SessionTokens.created_timedate)).limit(250).all()

    return orm_result

def list_all(before_date: int):
    """List all sessions for all users and user data
    Formatted in list of JSON, will list sessions even if matching user does not exist
    """
    
    orm_result = models.db.session.query(models.SessionTokens, models.User)\
        .join(models.User, models.SessionTokens.mattermost_id == models.User.mattermost_id, isouter=True)\
            .where(models.SessionTokens.created_timedate <= before_date)\
            .order_by(desc(models.SessionTokens.created_timedate)).limit(250).all()

    return orm_result