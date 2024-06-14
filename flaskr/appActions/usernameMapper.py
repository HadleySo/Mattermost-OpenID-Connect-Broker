import re
from .. import models
DB_USER_PATH = "flaskr/appData/user_idp_data.db"

def username_from_domain(domain_local:str):
    """Generates username from email address
    Checks if domain is listed in database and formats, otherwise return False

    :param domain_local: email address
    """
    domain_local = domain_local.strip()
    if domain_local.count("@") != 1:
        return False

    # Split up parts of email
    email_split = domain_local.split("@")
    local_address = email_split[0].lower()
    domain = email_split[1].lower()

    orm_result = models.db.session.query(models.DomainMapping).filter(models.DomainMapping.domain == domain).all()

    if len(orm_result) != 1:
        return False

    domain_settings = orm_result[0].__dict__

    # Check local part
    pattern = re.compile(domain_settings['local_regex'])
    if not pattern.fullmatch(local_address):
        return False
    
    preferred_username = domain_settings['username_prepend'] + local_address + domain_settings['username_append']

    preferred_username = preferred_username.lower()

    return preferred_username