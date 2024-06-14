from sqlalchemy import update

from .. import models

DB_PATH = "flaskr/appData/user_idp_data.db"

def handle_login(user_info: dict):
    """Check if user exists, if not create user
    Return dict of user JWT `preferred_username` 

    :param dict user_info: User data from Mattermost
    """
    import time
    since_epoch = int(time.time())
    id = user_info['id']

    preferred_username = get_jwt_preferred_username(id)

    if preferred_username == False:
        return {'preferred_username': False, 'error': "handle_login Domain ID invalid count"}

    # If user is new, create user
    if preferred_username == None:
        try_add = add_user(user_info, since_epoch)

        if try_add == False:
            return {'preferred_username': False, 'error': "handle_login domain invalid"}
        
        preferred_username = get_jwt_preferred_username(id)

        # If user could not be created, fail safe
        if preferred_username == None:
            return {'preferred_username': False, 'error': "handle_login unable to write user"}
    
    # Update last visit time
    update_user(user_info, since_epoch)
    
    return {'preferred_username': preferred_username}


def get_jwt_preferred_username(id: str) -> [None, bool, str]:
    """Get `preferred_username` field for JWT from database. The `preferred_username` contains domain prefix and postfix.
    If more than one id entry exists, return False
    If no record exists, return None

    :param str id: Mattermost user id
    """
    
    orm_result = models.db.session.query(models.User).filter(models.User.mattermost_id == id).all()

    if len(orm_result) > 1:
        return False
    elif len(orm_result) == 0:
        return None
    
    preferred_username = orm_result[0].__dict__['preferred_username']
    return preferred_username

def get_oidc(mattermost_id: str):
    """Get user info based on Mattermost ID, from database. Return in OIDC format and labels

    :param str mattermost_id: Mattermost user id
    """

    orm_result = models.db.session.query(models.User).filter(models.User.mattermost_id == mattermost_id).all()


    if len(orm_result) < 1:
        return False

    result_dict = orm_result[0].__dict__

    oidc_ready = {
        "sub": mattermost_id,
        "name": result_dict['first_name'] + " " + result_dict['last_name'],
        "given_name": result_dict['first_name'],
        "family_name": result_dict['last_name'],
        "preferred_username": result_dict['preferred_username'],
        "email": result_dict['email'],
        "updated_at": result_dict['create_at']
    }
    
    return oidc_ready

def get_admin_user_data(mattermost_id: str):
    """For admins, get user info based on Mattermost ID, from database. Data is sensitive.

    :param str mattermost_id: Mattermost user id
    """

    orm_result = models.db.session.query(models.User).filter(models.User.mattermost_id == mattermost_id).all()


    if len(orm_result) < 1:
        return False

    result_dict = orm_result[0].__dict__
    
    return result_dict

def get_local_id(mattermost_id: str):
    """Get local ID based on Mattermost ID

    :param str mattermost_id: Mattermost user id
    """

    orm_result = models.db.session.query(models.User).filter(models.User.mattermost_id == mattermost_id).all()

    if len(orm_result) == 0:
        raise Exception("Unable to converter Mattermost ID to local ID - zero")  
    if len(orm_result) != 1:
        raise Exception("Unable to converter Mattermost ID to local ID - not 1")  
    
    local_id = orm_result[0].__dict__['id']
    return local_id

def get_preferred_username(mattermost_id: str):
    """Get preferred_username based on Mattermost ID

    :param str mattermost_id: Mattermost user id
    """

    orm_result = models.db.session.query(models.User).filter(models.User.mattermost_id == mattermost_id).all()

    if len(orm_result) == 0:
        raise Exception("Unable to converter Mattermost ID to local ID - zero")  
    if len(orm_result) != 1:
        raise Exception("Unable to converter Mattermost ID to local ID - not 1")  
    
    local_id = orm_result[0].__dict__['preferred_username']
    return local_id

def update_user(user_info: dict, since_epoch: int) -> bool:
    """HELPER FUNC - Update user's last visit time, nickname, and MFA status from Mattermost data

    :param dict user_info: User data from Mattermost
    :param since_epoch: Timestamp of last visit in unix epoch
    """

    mattermost_id = user_info['id']
    nickname = user_info.get('nickname', "")
    mfa_active = user_info.get('mfa_active', False)
    
    stmt_01 = (update(models.User).where(models.User.mattermost_id == mattermost_id).values({"time_last_visit": since_epoch, "nickname": nickname, "mfa_active": mfa_active}))
    models.db.session.execute(stmt_01)
    models.db.session.commit()

    return True

def add_user(user_info: dict, since_epoch) -> bool:
    """HELPER FUNC - Add user to database

    :param user_info: Dictionary of user information from Mattermost
    :param since_epoch: Timestamp of last visit in unix epoch
    """

    from . import usernameMapper

    # Generate username
    preferred_username = usernameMapper.username_from_domain(user_info['email'])
    if preferred_username == False:
        return False
    
    # Create instance of User
    new_user = models.User(mattermost_id = user_info['id'], 
                        create_at = user_info['create_at'], 
                        preferred_username = preferred_username, 
                        email = user_info['email'], 
                        email_verified = user_info['email_verified'], 
                        nickname = user_info.get('nickname', ""), 
                        first_name = user_info['first_name'], 
                        last_name = user_info['last_name'],
                        mfa_active = user_info.get('mfa_active', False), 
                        time_last_visit = since_epoch, 
                        time_first_visit = since_epoch)

    models.db.session.add_all([new_user])
    models.db.session.commit()

    return True

def modify_user_display(user_info: dict) -> bool:
    """Update user's display name and nickname
    :param user_info: Dictionary of user information
    """

    mattermost_id = user_info['id']
    nickname = user_info.get('nickname', "")
    first_name = user_info.get('first_name', "")
    last_name = user_info.get('last_name', "")
    
    stmt_01 = (update(models.User).where(models.User.mattermost_id == mattermost_id).values({"nickname": nickname, "first_name": first_name, "last_name" : last_name}))
    models.db.session.execute(stmt_01)
    models.db.session.commit()

    return True

def list_all():
    """List all user data for all users
    Formatted in list of JSON
    """
    
    orm_result = models.db.session.query(models.User).all()

    return orm_result

