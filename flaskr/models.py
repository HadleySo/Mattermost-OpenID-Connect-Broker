from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2TokenMixin,
    OAuth2AuthorizationCodeMixin
)

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mattermost_id = db.Column(db.String(128), nullable=False)

    create_at = db.Column(db.BigInteger)
    preferred_username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    email_verified = db.Column(db.String(16))
    nickname = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    mfa_active = db.Column(db.Integer)
    time_last_visit = db.Column(db.Integer)
    time_first_visit = db.Column(db.Integer)
    

    def __str__(self):
        return self.mattermost_id

    def get_user_id(self):
        return self.id


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')

class SessionTokens(db.Model):
    __tablename__ = "ife_client_tokens"

    id = db.Column(db.Integer, primary_key=True)

    mattermost_id = db.Column(db.String(128), nullable=False)
    session_id = db.Column(db.String(128), nullable=False)
    valid = db.Column(db.Boolean, nullable=False)
    created_timedate = db.Column(db.Integer)

    ip_address = db.Column(db.String(64))
    cf_country = db.Column(db.String(64))
    user_agent = db.Column(db.String(1024))
    cf_ray = db.Column(db.String(128))

    cf_ipcity = db.Column(db.String(128))
    cf_iplongitude = db.Column(db.String(128))
    cf_iplatitude = db.Column(db.String(128))
    cf_region = db.Column(db.String(128))
    cf_timezone = db.Column(db.String(128))

class DomainMapping(db.Model):
    __tablename__ = "domain_mapping"

    id = db.Column(db.Integer, primary_key=True)

    domain = db.Column(db.String(128), nullable=False)
    local_regex = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    username_prepend = db.Column(db.String(128), nullable=False)
    username_append = db.Column(db.String(128), nullable=False)

