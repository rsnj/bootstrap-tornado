import hashlib
import yaml
try:
    import json
except ImportError:
    import simplejson as json

def _load_config():
    stream = open('config.yaml', 'r')
    return yaml.load(stream)

config = _load_config()

def hash_password(password):
    salt = config['password_salt']

    return hashlib.sha512(password + salt).hexdigest()


def _json_date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

def to_json(obj):
    return json.dumps(obj, default=_json_date_handler)

def from_json(json_str):
    return json.loads(json_str)