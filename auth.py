#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import inspect
import os
root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(root_path)
from functools import wraps
from flask import current_app as app
from flask import json, request
import datetime as dt
import jwt
import pandas as pd
import mailer_fn as mailer

from connections import connections
from data_fetching import verify_user_exists, verify_volunteer_exists


# In[ ]:



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1] if auth_header else ''
        if not auth_token:
            return json.dumps({'Response':{},'status':False,'string_response': 'User login required'})
        resp, success = decode_auth_token(auth_token)
        if not success:
            return json.dumps({'Response':{},'status':False,'string_response': resp})
        try:
            data = resp.split(' ', 1)
            user_id = data[0]
            access_type = data[1]
            org, user_exists = verify_user_exists(user_id, access_type)
            if not user_exists:
                return json.dumps({'Response':{},'status':False,'string_response': 'no valid user found'})
        except Exception:
            return json.dumps({'Response':{},'status':False,'string_response': 'no valid user found'})
        kwargs['user_id'] = user_id
        kwargs['organisation'] = org
        return f(*args, **kwargs)
    return decorated_function






def volunteer_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1] if auth_header else ''
        if not auth_token:
            return json.dumps({'Response':{},'status':False,'string_response': 'Volunteer login required'})
        resp, success = decode_auth_token(auth_token)
        if not success:
            return json.dumps({'Response':{},'status':False,'string_response': resp})
        try:
            data = resp.split(' ', 1)
            v_id = data[0]
            country = data[1]
            volunteer_exists = verify_volunteer_exists(None, v_id, country)
            if not volunteer_exists['status']:
                return json.dumps({'Response':{},'status':False,'string_response': 'no volunteer found'})
        except Exception:
            return json.dumps({'Response':{},'status':False,'string_response': 'no volunteer found'})
        kwargs['volunteer_id'] = v_id
        kwargs['organisation'] = volunteer_exists['source']
        return f(*args, **kwargs)
    return decorated_function


# In[ ]:


def encode_auth_token(key):
    try:
        payload = {
            'exp': dt.datetime.utcnow() + dt.timedelta(days=7),
            'iat': dt.datetime.utcnow(),
            'sub': str(key)
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        mailer.send_exception_mail()        
        return None


# In[ ]:



def decode_auth_token(auth_token):
    try:
        server_con = connections('prod_db_read')
        query = f"""select * from token_blacklist where token='{auth_token}'"""
        data = pd.read_sql(query, server_con)
        token_blacklisted = data.shape[0] > 0
        if token_blacklisted:
            return 'Token not allowed. Please log in again.', False
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return payload['sub'], True
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.', False
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.', False


# In[ ]:





# In[ ]:




