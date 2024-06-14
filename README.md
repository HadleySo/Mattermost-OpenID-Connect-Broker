# Mattermost OpenID Connect Broker

 [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Protocol mapping between OAuth2 and upstream OpenID Connect clients. Allows a self hosted [Mattermost](https://mattermost.com/) instance to provide authentication to upstream authorization management like [Keycloak](https://github.com/keycloak/keycloak) or [Authentik](https://github.com/goauthentik/authentik). 

Mattermost OpenID Connect Broker is meant to be used with [Keycloak](https://github.com/keycloak/keycloak) or [Authentik](https://github.com/goauthentik/authentik) with Mattermost OpenID Connect Broker acting as a middle layer; provides custom mappings for `preferred_username` based on email domains and pulls geolocation data from CloudFlare. 

This is a sanitized version of Illini Electric Motorsport's IdP & Authentication app, which came from Illini Formula Electric's Portal app - I made all three with similar functionality.

## Sign Out Behavior

When users sign out / visit the `/logout` endpoint Mattermost OpenID Connect Broker checks if a cookie called `authentik_session` exists. If the cookie exists the user is redirected to the Authentik default invalidation flow, with the Authentik domain configured in the `idp.cfg` file.

This requires that the default invalidation flow for Authentik redirect users to the Mattermost OpenID Connect Broker sign out endpoint after Authentik signs out. Otherwise the IdP session is not revoked when the user visits the `/logout` endpoint.

## Requirements

- Nginx Proxy
- CloudFlare
- MySQL / MariaDB
- Keycloak or Authentik (with invalidation flow redirecting to IdP sign out endpoint)

## Features

1. Consistent mapping of usernames for OpenID Connect based on user email addresses
1. OAuth2 client 
1. OpenID Connect provider (should only be used to connect to Keycloak or Authentik)
1. Whitelisted email domains and regex validation of email local parts
1. User revocation of sessions 
1. Admin revocation of other user sessions
1. 90 day retention of user session data

## Installing

1. Create a directory `/var/www/<YOUR_DIRECTORY>` and download this repo
2. Under `/var/www/<YOUR_DIRECTORY>` run the following:
    - Make a venv `python3 -m venv venv`
    - Activate the venv with `source venv/bin/activate`
    - In the venv install libraries `pip3 install -r requirements.txt`
3. Add the Flask app files and the Service files in their proper folders
    - Service file goes `/etc/systemd/system`
4. Randomly generate secret key and update `idp.cfg` app_secret_key under OAUTH
    - Do not save this key. Should be replaced on every reinstall
5. Init databases 
    - `flask db upgrade`
    - Connect to database and run [mysql_retention.sql](mysql_retention.sql)
6. Make RSA keys for JWT and save:
    - `ssh-keygen -t rsa -b 4096 -m PEM -f idp_rsa.key`
7. Set all settings in `idp.cfg`
8. Update logo images in `flaskr/static/images`
9. Add the nginx config, test, and reload
10. Start the system service `sudo systemctl start mm-oidc-broker`
11. Enable startup on boot `sudo systemctl enable mm-oidc-broker`
12. Direct proxy provider to socket: `/var/www/<YOUR_DIRECTORY>/mm_oidc_broker.sock`
13. Configure [Keycloak](https://github.com/keycloak/keycloak) or [Authentik](https://github.com/goauthentik/authentik)
14. Configure Authentik invalidation flow to redirect to Mattermost OpenID Connect Broker sign out endpoint `/logout`

## Configuration Settings

`idp_domain`: Where Mattermost OpenID Connect Broker will be accsible from. Domain (and port) without protocol.   
`sso_domain`: Top level domain, can be the same as `idp_domain` if a subdomain is not used for Mattermost OpenID Connect Broker.  
`mattermost_url`: Domain, protocol, and port of Mattermost instance.  
`authentik_domain`: Domain, protocol, and port of Authentik instance, if using Keycloak set to same value of `idp_domain`.  
`trusted_root`: Domains Mattermost OpenID Connect Broker is allowed to redirect to. Should be same as `sso_domain`.  


## Production Settings

Use Gunicorn:
- 3 workers
- Use venv and install directly in venv - [docs](https://docs.gunicorn.org/en/latest/deploy.html#using-virtualenv)

Limit requests for each worker to 50 before refresh

## Local Testing

`export FLASK_DEBUG=1`

Set the following in `idp.cfg`:  
`idp_domain = localhost:5000`  
`sso_domain = localhost:5000`  

If `ModuleNotFoundError: No module named 'flask_sqlalchemy'` appears, rehash your shell `hash -r`.


## Database Schema

Using Flask-Migrate, full schema available in [flaskr/models.py](flaskr/models.py)


## Error Messages

List of possible error messages:

| User message                                                            | Possible Issue                                                                                                               |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| MismatchingStateError                                                   | Authlib MismatchingStateError from JWT token received from Mattermost                                                        |
| MissingRequestTokenError                                                | Authlib request token is empty when calling authorize_access_token                                                           |
| MissingTokenError                                                       | Authlib MissingTokenError error when calling authorize_access_token                                                          |
| authorize_access_token Exception                                        | Authlib authorize_access_token function ran into an error when retrieving access token. More information is written to logs  |
| OAuth2 Token Invalid                                                    | access_token is missing after Authlib called authorize_access_token                                                          |
| OAuth2 user info error                                                  | Unable to get user info from OAuth2 user info endpoint                                                                       |
| Unable to convert session                                               | user_info from OAuth2 user info endpoint is invalid, or there is an issue with Flask sessions                                |
| Invalid attributes. Please set your first and last name, and try again. | User does not have both first and last name set                                                                              |
| handle_login Exception                                                  | Issue when calling handle_login. Most likely database connection issue                                                       |
| user_local_data handle_login Domain ID invalid count                    | Multiple users entries exist with the same Mattermost ID                                                                     |
| user_local_data handle_login domain invalid                             | The email domain is not on the approved list of domains                                                                      |
| user_local_data handle_login unable to write user                       | user_manager.add_user failed to create a user                                                                                |
| global_sso                                                              | Unable to create a instance of global SSO login credentials/cookie. May be issue reading CloudFlare headers or writing to DB |


## Verbiage

Use "sign in" & "sign out" not "log in" & "log out".   

Some older verbiage may be present that does not use the proper terms "sign in" & "sign out".

Reference https://ux.stackexchange.com/questions/1080/using-sign-in-vs-using-log-in and "Homepage Usability", Jakob Nielsen (together with Marie Tahir, 2002, p. 53) 

## License  

Mattermost OpenID Connect Broker is distributed under [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.txt).
