from datetime import datetime
from base import Model

class Invite(Model):
    id = None
    created = datetime.utcnow()
    code = None
    description = None
    total_count = 1
    redeemed_count = 0

class User(Model):
    _id = None
    created = datetime.utcnow()
    email = None
    password_hash = None
    invite_code = None
    facebook_id = None
    twitter_id = None
    screen_name = None
    birth_date = None
    zipcode = None
    gender = 0
    opt_in = False
