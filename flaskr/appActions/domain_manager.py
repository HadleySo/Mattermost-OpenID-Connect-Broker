from .. import models

def list_all():
    """List all domains and their mappings
    """
    orm_result = models.db.session.query(models.DomainMapping).all()

    return orm_result

def add(domain: str, local_regex: str, display_name: str = "", username_prepend: str = "", username_append: str = "") -> bool:
    """Add domain to database

    :param domain: FQDN of email addresses
    :param local_regex: Regex to validate local part of email
    :param display_name: Name to display
    :param username_prepend: Text to put before local email part for domain username
    :param username_append: Text to put after local email part for domain username
    """

    import re

    domain = domain.lower()

    # Check if domain is valid
    domain_regex = "^((?!-)[A-Za-z0-9-]" + "{1,63}(?<!-)\\.)" +"+[A-Za-z]{2,6}"     
    domain_regex_c = re.compile(domain_regex)
    if (domain == None):
        return False
    if not (re.search(domain_regex_c, domain)):
        return False

    # Check that domain doesn't exist already
    orm_result = models.db.session.query(models.DomainMapping).filter(models.DomainMapping.domain == domain).all()

    if len(orm_result) != 0:
        return False

    new_domain = models.DomainMapping(domain = domain,
                                    local_regex = local_regex,
                                    display_name = display_name,
                                    username_prepend = username_prepend,
                                    username_append = username_append)

    models.db.session.add_all([new_domain])
    models.db.session.commit()

    return True