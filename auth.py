from functools import wraps
from flask import current_app as app
from flask import json, request
import datetime as dt
import jwt
import pandas as pd

from connections import connections


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1] if auth_header else ''
        if not auth_token:
            return json.dumps({'Response':{},'status':False,'string_response': 'Please login to view data'})
        resp, success = decode_auth_token(auth_token)
        if not success:
            return json.dumps({'Response':{},'status':False,'string_response': resp})

        return f(*args, **kwargs)
    return decorated_function


def encode_auth_token(user_id):
    try:
        payload = {
            'exp': dt.datetime.utcnow() + dt.timedelta(days=1),
            'iat': dt.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return None


def decode_auth_token(auth_token):
    try:
        server_con = connections('prod_db_read')
        query = f"""select * from token_blacklist where token='{auth_token}'"""
        data = pd.read_sql(query, server_con)
        token_blacklisted = data.shape[0] > 0
        if token_blacklisted:
            return 'Invalid token. Please log in again.', False
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return payload['sub'], True
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.', False
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.', False
