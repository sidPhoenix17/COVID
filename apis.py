#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
from flask import Flask, request, jsonify, json
from flask_cors import CORS
from celery import Celery
import urllib
import os
import uuid

from connections import connections

from database_entry import add_requests, add_volunteers_to_db, contact_us_form_add, verify_user, \
    add_user, request_matching, update_requests_db, update_volunteers_db, \
    blacklist_token, send_sms, send_otp, resend_otp, verify_otp, update_nearby_volunteers_db, \
    add_request_verification_db, update_request_v_db, update_request_status

from data_fetching import get_ticker_counts, get_private_map_data, get_public_map_data, get_user_id, \
    accept_request_page, request_data_by_uuid, request_data_by_id, volunteer_data_by_id, \
    website_requests_display, get_requests_list, get_source_list, website_success_stories, \
    verify_volunteer_exists, check_past_verification, get_volunteers_assigned_to_request, \
    get_type_list, get_moderator_list, get_unverified_requests, get_requests_assigned_to_volunteer, \
    accept_request_page_secure, get_assigned_requests, get_user_messages, user_data_by_id

from partner_assignment import generate_uuid, message_all_volunteers

from auth import encode_auth_token, decode_auth_token, login_required, volunteer_login_req

from utils import capture_api_exception

from message_templates import old_reg_sms, new_reg_sms,new_request_sms,new_request_mod_sms, request_verified_sms, \
    request_accepted_v_sms, request_accepted_r_sms, request_accepted_m_sms, request_rejected_sms, \
    request_closed_v_sms, request_closed_r_sms, request_closed_m_sms,a_request_closed_v_sms, a_request_closed_r_sms, a_request_closed_m_sms

from settings import server_type, SECRET_KEY, neighbourhood_radius, search_radius

import mailer_fn as mailer
import cred_config as cc

# In[ ]:


# Allow edit of source from verification page
# Allow user to enter urgent (immediate, needed in <24 hours)/not urgent (needed in 24-48 hours)
# Allow users to see urgent requests


# In[ ]:


def datetime_converter(o):
    if isinstance(o, dt.datetime):
        return dt.datetime.strftime(o, '%a, %d %b %y, %I:%M%p %Z')


# In[ ]:


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = SECRET_KEY


# In[ ]:


# app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

# @celery.task
# def async_task():
#     print("1234")
#     print(dt.datetime.now())


# @app.route('/test_async',methods=['GET'])
# def test_async():
#     try:
#         async_task.delay()
#     except Exception as e:
#         response = {'Response':str(e),'status':200,'string_response':'Ok'}
#         return json.dumps(response)
#     response = {'Response':{'key': 'Ok'},'status':200,'string_response':'Ok'}
#     return json.dumps(response)


# In[ ]:


# @celery.task
# def volunteer_request(lat,lon,radius,search_radius,uuid):
#     print('Running volunteer_request function at ', dt.datetime.now())
#     message_all_volunteers(uuid,radius,search_radius)
#     return None


# @celery.task
# def no_volunteer_assigned(lat,lon,radius,uuid):
#     print('Running no_volunteer_assigned function at ', dt.datetime.now())
#     r_df = request_data_by_uuid(uuid)
#     if(r_df['status']=='pending'):
#         sms_text = "No Volunteer assigned to "+r_df.loc[0,'name']
#         for i_number in moderator_list:
#             send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
#     return None


# In[ ]:


# For Request/Help form submission.
@app.route('/create_request', methods=['POST'])
@capture_api_exception
def create_request():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id', '')
    age = request.form.get('age')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    user_request = request.form.get('request')
    latitude = request.form.get('latitude', 0.0)
    longitude = request.form.get('longitude', 0.0)
    source = request.form.get('source', 'covidsos')
    status = request.form.get('status', 'received')
    country = request.form.get('country', 'India')
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    uuid = generate_uuid()
    req_dict = {'timestamp': [current_time], 'name': [name], 'mob_number': [mob_number], 'email_id': [email_id],
                'country': [country], 'address': [address], 'geoaddress': [geoaddress], 'latitude': [latitude],
                'longitude': [longitude],
                'source': [source], 'age': [age], 'request': [user_request], 'status': [status], 'uuid': [uuid]}
    df = pd.DataFrame(req_dict)
    df['email_id'] = df['email_id'].fillna('')
    expected_columns = ['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude',
                        'longitude', 'source', 'request', 'age', 'status', 'uuid']
    x, y = add_requests(df)
    response = {'Response': {}, 'status': x, 'string_response': y}
    if (x):
        # move to async
        sms_text = new_request_sms.format(name=name,source=source)
        send_sms(sms_text, sms_to=int(mob_number), sms_type='transactional', send=True)
        mod_sms_text = new_request_mod_sms.format(source=source, uuid=str(uuid))
        moderator_list = get_moderator_list()
        for i_number in moderator_list:
            send_sms(mod_sms_text, sms_to=int(i_number), sms_type='transactional', send=True)
    return json.dumps(response)


# In[ ]:


@app.route('/create_volunteer', methods=['POST'])
@capture_api_exception
def add_volunteer():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id', '')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    latitude = request.form.get('latitude', 0.0)
    longitude = request.form.get('longitude', 0.0)
    source = request.form.get('source')
    status = request.form.get('status', 1)
    country = request.form.get('country', 'India')
    support_type = request.form.get('support_type', '1,2,3,4,5')
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    req_dict = {'timestamp': [current_time], 'name': [name], 'mob_number': [mob_number], 'email_id': [email_id],
                'country': [country], 'address': [address], 'geoaddress': [geoaddress], 'latitude': [latitude],
                'longitude': [longitude],
                'source': [source], 'status': [status], 'support_type': [support_type]}
    df = pd.DataFrame(req_dict)
    expected_columns = ['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude',
                        'longitude', 'source', 'status', 'support_type']
    x, y = add_volunteers_to_db(df)
    if (x):
        if (y == 'Volunteer already exists. Your information has been updated'):
            v_sms_text = old_reg_sms
        else:
            v_sms_text = new_reg_sms
        send_sms(v_sms_text, sms_to=int(mob_number), sms_type='transactional', send=True)
    response = {'Response': {}, 'status': x, 'string_response': y}
    return json.dumps(response)


# In[ ]:


@app.route('/login', methods=['POST'])
@capture_api_exception
def login_request():
    name = request.form.get('username')
    password = request.form.get('password')
    response = verify_user(name, password)
    user_id, access_type = get_user_id(name, password)
    if not user_id:
        return {'Response': {}, 'status': False, 'string_response': 'Failed to find user.'}
    response['Response']['auth_token'] = encode_auth_token(f'{user_id} {access_type}').decode()
    return json.dumps(response)

# In[ ]:


@app.route('/new_user', methods=['POST'])
@capture_api_exception
@login_required
def new_user(*args, **kwargs):
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    password = request.form.get('password')
    organisation = request.form.get('organisation')
    auth_user_org = kwargs.get('organisation')
    creator_access_type = request.form.get('creator_access_type')
    user_access_type = request.form.get('user_access_type')
    creator_user_id = request.form.get('creator_user_id')
    verification_team = request.form.get('verification_team', 1)
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    if auth_user_org != 'covidsos' and auth_user_org != organisation:
        return {'Response': {}, 'status': False, 'string_response': 'You cannot create a user of another organisation.'}
    if (user_access_type == 'moderator'):
        access_type = 2
    elif (user_access_type == 'viewer'):
        access_type = 3
    elif (user_access_type == 'superuser'):
        response = {'Response': {}, 'status': False, 'string_response': 'You cannot create superuser'}
        return json.dumps(response)
    else:
        response = {'Response': {}, 'status': False, 'string_response': 'Invalid access type'}
        return json.dumps(response)
    req_dict = {'creation_date': [current_time], 'name': [name], 'mob_number': [mob_number], 'email_id': [email_id],
                'organisation': [organisation], 'password': [password], 'access_type': [access_type],
                'created_by': [creator_user_id], 'verification_team': [verification_team]}
    df = pd.DataFrame(req_dict)
    if (creator_access_type == 'superuser'):
        response = add_user(df)
        user_id, access_type = get_user_id(mob_number, password)
        if not user_id:
            return {'Response': {}, 'status': False, 'string_response': 'Failed to create user. Please try again later'}
        response['auth_token'] = encode_auth_token(f'{user_id} {access_type}').decode()
    else:
        response = {'Response': {}, 'status': False,
                    'string_response': 'User does not have permission to create new users'}
    return json.dumps(response)

# In[ ]:


@app.route('/reachout_form', methods=['POST'])
@capture_api_exception
def add_org_request():
    name = request.form.get('name')
    organisation = request.form.get('organisation')
    email_id = request.form.get('email_id')
    mob_number = request.form.get('mob_number')
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    comments = request.form.get('comments')
    req_dict = {'timestamp': [current_time], 'name': [name], 'organisation': [organisation], 'mob_number': [mob_number],
                'email_id': [email_id],
                'source': ['website'], 'comments': [comments]}
    df = pd.DataFrame(req_dict)
    expected_columns = ['timestamp', 'name', 'organisation', 'mob_number', 'email_id', 'source', 'comments']
    x, y = contact_us_form_add(df)
    response = {'Response': {}, 'status': x, 'string_response': y}
    return json.dumps(response)


# In[ ]:


@app.route('/top_ticker', methods=['GET'])
@capture_api_exception
def ticker_counts():
    response = get_ticker_counts()
    return json.dumps(response)

# In[ ]:


@app.route('/request_status_list', methods=['GET'])
@capture_api_exception
def request_status_list():
    response = get_requests_list()
    return json.dumps(response)


# In[ ]:


@app.route('/source_list', methods=['GET'])
@capture_api_exception
def request_source_list():
    response = get_source_list()
    return json.dumps(response)


# In[ ]:


@app.route('/support_type_list', methods=['GET'])
@capture_api_exception
def support_type_list():
    get_type = request.args.get('type')
    if ((get_type == 'volunteer') or (get_type == 'request')):
        response = get_type_list(get_type)
        return json.dumps(response)
    else:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Incorrect response'})

# In[ ]:


@app.route('/private_map_data', methods=['GET'])
@capture_api_exception
@login_required
def private_map_data(*args, **kwargs):
    org = kwargs.get('organisation', '')
    response = get_private_map_data(org)
    return json.dumps({'Response': response, 'status': True, 'string_response': 'Full data sent'},
                        default=datetime_converter)


# In[ ]:


@app.route('/public_map_data', methods=['GET'])
@capture_api_exception
def public_map_data():
    response = get_public_map_data()
    return json.dumps({'Response': response, 'status': True, 'string_response': 'Public data sent'})


# In[ ]:


@app.route('/assign_volunteer', methods=['POST'])
@capture_api_exception
@login_required
def assign_volunteer(*args, **kwargs):
    org = kwargs.get('organisation', '')
    volunteer_id = request.form.get('volunteer_id')
    request_id = request.form.get('request_id')
    #TODO:
    # Change matched_by to use user_id/volunteer_id from kwargs instead of form data
    # change matched_by datatype to int and convert all existing values to be numeric
    matched_by = request.form.get('matched_by')
    response = assign_request_to_volunteer(volunteer_id, request_id, matched_by, org)
    return json.dumps(response)


@app.route('/assign_request', methods=['POST'])
@capture_api_exception
@volunteer_login_req
def assign_request(*args, **kwargs):
    volunteer_id = kwargs.get('volunteer_id')
    request_id = request.form.get('request_id')
    matched_by = request.form.get('matched_by', 0)
    response = assign_request_to_volunteer(volunteer_id, request_id, matched_by,'covidsos')
    return json.dumps(response)


def assign_request_to_volunteer(volunteer_id, request_id, matched_by,org):
    r_df = request_data_by_id(request_id)
    v_df = volunteer_data_by_id(volunteer_id)
    if (r_df.shape[0] == 0):
        return {'status': False, 'string_response': 'Request ID does not exist.', 'Response': {}}
    if (v_df.shape[0] == 0):
        return {'status': False, 'string_response': 'Volunteer does not exist', 'Response': {}}
    else:
        if org != 'covidsos' and not (r_df.loc[0, 'source'] == v_df.loc[0, 'source'] == org):
            return {'status': False, 'string_response': 'Organisation not same for all: requester, volunteer and matchmaker', 'Response': {}}
        if (r_df.loc[0, 'status'] in ['received', 'verified', 'pending']):
            current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
            req_dict = {'volunteer_id': [volunteer_id], 'request_id': [r_df.loc[0, 'r_id']],
                        'matching_by': [matched_by], 'timestamp': [current_time]}
            df = pd.DataFrame(req_dict)
            # Add entry in request_matching table
            response = request_matching(df)
            # Update request status as matched
            if response['status'] == True:
                volunteers_assigned = get_volunteers_assigned_to_request(request_id)
                if r_df.loc[0, 'volunteers_reqd'] == volunteers_assigned:
                    response_2 = update_requests_db({'id': request_id}, {'status': 'matched'})
                    response_3 = update_nearby_volunteers_db({'r_id': request_id}, {'status': 'expired'})
            # Send to Volunteer
            v_sms_text = request_accepted_v_sms.format(r_name=r_df.loc[0, 'name'],mob_number=r_df.loc[0, 'mob_number'],request=r_df.loc[0, 'request'],address=r_df.loc[0, 'geoaddress'])
            send_sms(v_sms_text, int(v_df.loc[0, 'mob_number']), sms_type='transactional', send=True)
            # Send to Requestor
            r_sms_text = request_accepted_r_sms.format(v_name=v_df.loc[0,'name'],mob_number=v_df.loc[0,'mob_number'])
            send_sms(r_sms_text, int(r_df.loc[0, 'mob_number']), sms_type='transactional', send=True)
            # Send to Moderator
            m_sms_text = request_accepted_m_sms.format(v_name=v_df.loc[0,'name'],v_mob_number=v_df.loc[0,'mob_number'],r_name=r_df.loc[0, 'name'],r_mob_number=r_df.loc[0, 'mob_number'])
            moderator_list = get_moderator_list()
            for i_number in moderator_list:
                send_sms(m_sms_text, int(i_number), sms_type='transactional', send=True)
        else:
            return {'status': False, 'string_response': 'Request already assigned/closed/completed', 'Response': {}}
    return response


# In[ ]:


@app.route('/auto_assign_volunteer', methods=['POST'])
@capture_api_exception
def auto_assign_volunteer():
    v_id = request.form.get('volunteer_id')
    uuid = request.form.get('uuid')
    matching_by = 'autoassigned'
    task_action = request.form.get('task_action')
    r_df = request_data_by_uuid(uuid)
    v_df = volunteer_data_by_id(v_id)
    if (r_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Request ID does not exist.', 'Response': {}})
    if (v_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Volunteer does not exist', 'Response': {}})
    else:
        r_id = r_df.loc[0, 'r_id']
        if (((r_df.loc[0, 'status'] == 'received') or (r_df.loc[0, 'status'] == 'verified') or (
                r_df.loc[0, 'status'] == 'pending')) & (task_action == 'accepted')):
            current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
            req_dict = {'volunteer_id': [v_id], 'request_id': [r_id], 'matching_by': [matching_by],
                        'timestamp': [current_time]}
            df = pd.DataFrame(req_dict)
            response = request_matching(df)
            response_2 = update_requests_db({'id': r_id}, {'status': 'matched'})
            response_3 = update_nearby_volunteers_db({'r_id': r_id}, {'status': 'expired'})
            # Send to Volunteer
            v_sms_text = request_accepted_v_sms.format(r_name=r_df.loc[0, 'name'],mob_number=r_df.loc[0, 'mob_number'],request=r_df.loc[0, 'request'],address=r_df.loc[0, 'geoaddress'])
            send_sms(v_sms_text, int(v_df.loc[0, 'mob_number']), sms_type='transactional', send=True)
            # Send to Requestor
            r_sms_text = request_accepted_r_sms.format(v_name=v_df.loc[0, 'name'], mob_number=v_df.loc[0, 'mob_number'])
            send_sms(r_sms_text, int(r_df.loc[0, 'mob_number']), sms_type='transactional', send=True)
            return json.dumps(response)
        elif ((r_df.loc[0, 'status'] == 'received') or (r_df.loc[0, 'status'] == 'verified') or (
                r_df.loc[0, 'status'] == 'pending')):
            response_3 = update_nearby_volunteers_db({'r_id': r_id, 'v_id': v_id}, {'status': 'expired'})
            return json.dumps({'status': True, 'string_response': 'Request rejected', 'Response': {}})
        else:
            return json.dumps({'status': False, 'string_response': 'Request already assigned', 'Response': {}})


# In[ ]:


@app.route('/update_request_info', methods=['POST'])
@capture_api_exception
@login_required
def update_request_info(*args, **kwargs):
    r_id = request.form.get('request_id')
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    age = request.form.get('age')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    user_request = request.form.get('request')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    source = request.form.get('source')
    auth_user_org = kwargs.get('organisation')
    status = request.form.get('status')
    country = request.form.get('country')
    r_df = request_data_by_id(r_id)
    if (r_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Request ID does not exist.', 'Response': {}})
    if auth_user_org != 'covidsos' and r_df.loc[0, 'source'] != auth_user_org:
        return json.dumps({'status': False, 'string_response': 'Your organisation does not match that of this request.', 'Response': {}})
    req_dict = {'name': name, 'mob_number': mob_number, 'email_id': email_id,
                'country': country, 'address': address, 'geoaddress': geoaddress, 'latitude': latitude,
                'longitude': longitude,
                'source': source, 'age': age, 'request': user_request, 'status': status}
    if (r_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Request does not exist', 'Response': {}})
    if (r_id is None):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Request ID mandatory'})
    r_dict = {x: req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_requests_db({'id': r_id}, r_dict))
    return response


# In[ ]:


# @app.route('/volunteer_api',methods=['GET'])
# @volunteer_login_req
# def volunteer_login_check(*args,**kwargs):
#     print(kwargs['volunteer_id'])
#     return json.dumps({'status':True,'string_response':'Volunteer is logged in','Response':{}})


# In[ ]:


@app.route('/update_volunteer_info', methods=['POST'])
@capture_api_exception
@login_required
def update_volunteer_info(*args, **kwargs):
    v_id = request.form.get('volunteer_id')
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    source = request.form.get('source')
    auth_user_org = kwargs.get('organisation', '')
    status = request.form.get('status')
    country = request.form.get('country')
    req_dict = {'name': name, 'mob_number': mob_number, 'email_id': email_id,
                'country': country, 'address': address, 'geoaddress': geoaddress, 'latitude': latitude,
                'longitude': longitude,
                'source': source, 'status': status}
    v_df = volunteer_data_by_id(v_id)
    if (v_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Volunteer does not exist', 'Response': {}})
    if auth_user_org != 'covidsos' and v_df.loc[0, 'source'] != auth_user_org:
        return json.dumps({'status': False, 'string_response': 'Your organisation does not match that of this volunteer.', 'Response': {}})
    if (v_id is None):
        return {'Response': {}, 'status': False, 'string_response': 'Volunteer ID mandatory'}
    v_dict = {x: req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_volunteers_db({'id': v_id}, v_dict))
    return response


# In[ ]:


@app.route('/logout',methods=['POST'])
@capture_api_exception
def logout_request():
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(" ")[1] if auth_header else ''
    if not auth_token:
        return json.dumps({'Response':{},'status':False,'string_response': 'No valid login found'})
    resp, success = decode_auth_token(auth_token)
    if not success:
        return json.dumps({'Response':{},'status':False,'string_response': 'No valid login found'})
    success = blacklist_token(auth_token)
    message = 'Logged out successfully' if success else 'Failed to logout'
    return json.dumps({'Response': {}, 'status': success, 'string_response': message})


# In[ ]:


# get requests that are available to be assigned to volunteers
@app.route('/accept_page', methods=['GET'])
@capture_api_exception
def request_accept_page():
    uuid = request.args.get('uuid')
    df = accept_request_page(uuid)
    if (df.shape[0] == 0):
        return json.dumps(
            {'Response': {}, 'status': False, 'string_response': 'This page does not exist. Redirecting to homepage'})
    else:
        return json.dumps(
            {'Response': df.to_dict('records'), 'status': True, 'string_response': 'Request related data extracted'})


# In[ ]:
@app.route('/create_ngo_request', methods=['POST'])
@capture_api_exception
@login_required
def ngo_request_form(*args, **kwargs):
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id', '')
    age = request.form.get('age', 70)
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    user_request = request.form.get('request')
    latitude = request.form.get('latitude', 0.0)
    longitude = request.form.get('longitude', 0.0)
    source = request.form.get('source', 'covidsos')
    if((source=='undefined')or(source=='')):
        source='covidsos'
    status = request.form.get('status', 'received')
    if(status==''):
        status='received'
    country = request.form.get('country', 'India')
    uuid = generate_uuid()
    what = request.form.get('what')
    why = request.form.get('why')
    financial_assistance = request.form.get('financial_assistance', 0)
    verification_status = 'pending'
    where = geoaddress
    verified_by = kwargs.get('user_id', 0)
    urgent_status = request.form.get('urgent', 'no')
    volunteers_reqd = request.form.get('volunteer_count', 1)
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    req_dict = {'timestamp': [current_time], 'name': [name], 'mob_number': [mob_number], 'email_id': [email_id],
                'country': [country], 'address': [address], 'geoaddress': [geoaddress], 'latitude': [latitude],
                'longitude': [longitude],
                'source': [source], 'age': [age], 'request': [user_request], 'status': [status], 'uuid': [uuid],
                'volunteers_reqd': [volunteers_reqd]}
    df = pd.DataFrame(req_dict)
    df['email_id'] = df['email_id'].fillna('')
    expected_columns = ['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude',
                        'longitude', 'source', 'request', 'age', 'status', 'uuid']
    x1, y1 = add_requests(df[expected_columns])
    r_df = request_data_by_uuid(uuid)
    r_v_dict = {'r_id': [r_df.loc[0, 'r_id']], 'why': [why], 'what': [what], 'where': [where],
                'verification_status': [verification_status], 'verified_by': [verified_by], 'timestamp': [current_time],
                'financial_assistance': [financial_assistance], 'urgent': [urgent_status]}
    df = pd.DataFrame(r_v_dict)
    expected_columns = ['timestamp', 'r_id', 'what', 'why', 'where', 'verification_status', 'verified_by',
                        'financial_assistance', 'urgent']
    x2, y2 = add_request_verification_db(df[expected_columns])
    if (x1):
        # move to async
        sms_text = new_request_sms.format(source=source, name=name)
        send_sms(sms_text, sms_to=int(mob_number), sms_type='transactional', send=True)
        mod_sms_text = new_request_mod_sms.format(source=source, uuid=str(uuid))
        moderator_list = get_moderator_list()
        for i_number in moderator_list:
            send_sms(mod_sms_text, sms_to=int(i_number), sms_type='transactional', send=True)

    response = {'Response': {}, 'status': x1, 'string_response': y1}
    return response


# Get request data by uuid along with its existing verification data
# TODO: Change method to GET
@app.route('/verify_request_page', methods=['POST'])
@capture_api_exception
@login_required
def verify_request_page(*args, **kwargs):
    uuid = request.form.get('uuid')
    auth_user_org = kwargs.get('organisation', '')
    r_df = request_data_by_uuid(uuid)
    c_1 = ['r_id', 'name', 'mob_number', 'geoaddress', 'latitude', 'longitude', 'request', 'status', 'timestamp', 'source']
    # Check if request verification table already has a row, then also send info from request verification data along with it.
    if (r_df.shape[0] == 0):
        return json.dumps({'status': False, 'string_response': 'Request ID does not exist.', 'Response': {}})
    if auth_user_org != 'covidsos' and r_df.loc[0, 'source'] != auth_user_org:
        return json.dumps({'status': False, 'string_response': 'Your organisation and that of the request dont match.', 'Response': {}})
    past_df, past_status = check_past_verification(str(r_df.loc[0,'r_id']))
    c_2 = ['id','r_id','why','what','request_address','verification_status','urgent','financial_assistance']
    if(past_status):
        ngo_request = {'status':True,'additional_data':past_df.loc[0].to_dict()}
    else:
        ngo_request = {'status':False,'additional_data':{}}
    if (r_df.loc[0, 'status'] == 'received'):
        return json.dumps(
            {'Response': r_df.to_dict('records'), 'status': True, 'string_response': 'Request data extracted','ngo_request':ngo_request},
            default=datetime_converter)
    else:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Request already verified/rejected'})

# In[ ]:


# mark verified/rejected and create a verification table entry with verification data
@app.route('/verify_request', methods=['POST'])
@capture_api_exception
@login_required
def verify_request(*args, **kwargs):
    uuid = request.form.get('uuid')
    what = request.form.get('what')
    why = request.form.get('why')
    financial_assistance = request.form.get('financial_assistance', 0)
    verification_status = request.form.get('verification_status')
    verified_by = kwargs.get('user_id', 0)
    r_id = request.form.get('r_id')
    name = request.form.get('name')
    where = request.form.get('geoaddress')
    mob_number = request.form.get('mob_number')
    urgent_status = request.form.get('urgent', 'no')
    auth_user_org = kwargs.get('organisation', '')
    source = request.form.get('source', 'covidsos')
    if (source == 'undefined'):
        source = 'covidsos'
    volunteers_reqd = request.form.get('volunteer_count', 1)
    current_time = dt.datetime.utcnow() + dt.timedelta(minutes=330)
    if (verification_status is None):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Please send verification status'})
    if ((r_id is None) or (uuid is None)):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Please send UUID/request ID'})
    r_df = request_data_by_uuid(uuid)
    if auth_user_org != 'covidsos' and r_df.loc[0, 'source'] != auth_user_org:
        return json.dumps({'status': False, 'string_response': 'Your organisation and that of the request dont match.', 'Response': {}})
    if (r_df.shape[0] == 0):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Invalid UUID/request ID'})
    if (r_df.loc[0, 'source'] != source):
        response_0 = update_requests_db({'uuid': uuid}, {'source': source})
    if (r_df.loc[0, 'status'] == 'received'):
        r_v_dict = {'r_id': [r_id], 'why': [why], 'what': [what], 'where': [where],
                    'verification_status': [verification_status], 'verified_by': [verified_by],
                    'timestamp': [current_time], 'financial_assistance': [financial_assistance],
                    'urgent': [urgent_status]}
        df = pd.DataFrame(r_v_dict)
        expected_columns = ['timestamp', 'r_id', 'what', 'why', 'where', 'verification_status', 'verified_by',
                            'financial_assistance', 'urgent']
        response_2 = update_requests_db({'uuid': uuid},
                                        {'status': verification_status, 'volunteers_reqd': volunteers_reqd})
        print('updated the status')
        past_df, past_status = check_past_verification(str(r_id))
        if (past_status == True):
            r_v_dict = {'r_id': r_id, 'why': why, 'what': what, 'where': where,
                        'verification_status': verification_status, 'verified_by': verified_by,
                        'timestamp': current_time, 'financial_assistance': financial_assistance,
                        'urgent': urgent_status}
            rv_dict = {x: r_v_dict[x] for x in r_v_dict}
            update_request_v_db({'id': (past_df.loc[0,'id'])}, rv_dict)
        else:
            x, y = add_request_verification_db(df)
        if (verification_status == 'verified'):
            requestor_text = request_verified_sms
            send_sms(requestor_text, sms_to=int(mob_number), sms_type='transactional', send=True)
            message_all_volunteers(uuid, neighbourhood_radius, search_radius)
        else:
            requestor_text = request_rejected_sms
            send_sms(requestor_text, sms_to=int(mob_number), sms_type='transactional', send=True)
        return json.dumps(
            {'Response': {}, 'status': response_2['status'], 'string_response': response_2['string_response']})
    else:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Request already verified/rejected'})


# In[ ]:


@app.route('/pending_requests', methods=['GET'])
@capture_api_exception
def pending_requests():
    response = website_requests_display()
    return json.dumps({'Response': response, 'status': True, 'string_response': 'Request data extracted'},
                        default=datetime_converter)


# In[ ]:


@app.route('/unverified_requests', methods=['GET'])
@capture_api_exception
@login_required
def unverified_requests(*args, **kwargs):
    org = kwargs.get('organisation', '')
    df = get_unverified_requests(org)
    if (df.shape[0] > 0):
        return json.dumps(
            {'Response': df.to_dict('records'), 'status': True, 'string_response': 'Request data extracted'},
            default=datetime_converter)
    else:
        return json.dumps({'Response': {}, 'status': True, 'string_response': 'No unverified requests found'},
                            default=datetime_converter)


# In[ ]:

@app.route('/accepted_requests', methods=['GET'])
@capture_api_exception
@login_required
def assigned_requests(*args, **kwargs):
    org = kwargs.get('organisation', '')
    df = get_assigned_requests(org)
    if (df.shape[0] > 0):
        return json.dumps(
            {'Response': df.to_dict('records'), 'status': True, 'string_response': 'Request data extracted'},
            default=datetime_converter)
    else:
        return json.dumps({'Response': {}, 'status': True, 'string_response': 'No open requests found'},
                            default=datetime_converter)


# In[ ]:


@app.route('/success_stories', methods=['GET'])
@capture_api_exception
def success_stories():
    response = website_success_stories()
    return json.dumps({'Response': response, 'status': True, 'string_response': 'Success stories data extracted'})


# In[ ]:


@app.route('/request_otp', methods=['POST'])
@capture_api_exception
def send_otp_request():
    mob_number = request.form.get('mob_number')
    if not verify_volunteer_exists(mob_number)['status']:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'No user found for this mobile number'})
    response, success = send_otp(mob_number)
    return json.dumps({'Response': {}, 'status': success, 'string_response': response})

@app.route('/resend_otp', methods=['POST'])
@capture_api_exception
def resend_otp_request():
    mob_number = request.form.get('mob_number')
    if not verify_volunteer_exists(mob_number)['status']:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'No user found for this mobile number'})
    response, success = resend_otp(mob_number)
    return json.dumps({'Response': {}, 'status': success, 'string_response': response})


@app.route('/verify_otp', methods=['POST'])
@capture_api_exception
def verify_otp_request():
    mob_number = request.form.get('mob_number')
    otp = request.form.get('otp')
    userData = verify_volunteer_exists(mob_number)
    if not userData['status']:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'No user found for this mobile number'})
    response, success = verify_otp(otp, mob_number)
    responseObj = {}
    if success:
        user_id = int(str(userData['volunteer_id']))
        country = userData['country']
        name = userData['name']
        encodeKey = f'{user_id} {country}'
        responseObj = {'auth_token': encode_auth_token(encodeKey).decode(), 'name': name, 'volunteer_id': user_id}
    return json.dumps({'Response': responseObj, 'status': success, 'string_response': response})


# In[ ]:


@app.route('/volunteer-requests', methods=['GET'])
@capture_api_exception
@volunteer_login_req
def volunteer_tickets(*args, **kwargs):
    volunteer_id = kwargs['volunteer_id']
    volunteer_reqs = get_requests_assigned_to_volunteer(volunteer_id)
    return json.dumps({'Response': volunteer_reqs, 'status': True, 'string_response': 'Data sent'})


@app.route('/request-info', methods=['GET'])
@capture_api_exception
@volunteer_login_req
def get_request_info(*args, **kwargs):
    request_uuid = request.args.get('uuid', '')
    request_data = accept_request_page_secure(request_uuid)
    request_data = request_data.to_dict('records')
    return json.dumps({'Response': request_data, 'status': True, 'string_response': 'Data sent'})


@app.route('/vol-update-request', methods=['POST'])
@capture_api_exception
@volunteer_login_req
def task_completed(*args, **kwargs):
    volunteer_id = kwargs['volunteer_id']
    request_uuid = request.form.get('request_uuid')
    status = request.form.get('status')
    status_message = request.form.get('status_message', '')
    v_df = volunteer_data_by_id(volunteer_id)
    r_df = request_data_by_uuid(request_uuid)
    if status not in ['completed', 'completed externally', 'cancelled', 'reported']:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'invalid status value'})
    if(status == r_df.loc[0,'status']):
        return json.dumps({'Response':{},'status':False,'string_response':'Request Status Already updated'})
    response, success = update_request_status(request_uuid, status, status_message, volunteer_id)
    # Send SMS to Volunteer, Requestor and Moderator - request_closed_v_sms,request_closed_r_sms,request_closed_m_sms
    if((v_df.shape[0]>0)&(r_df.shape[0]>0)):
        send_sms(request_closed_v_sms.format(status=status),int(v_df.loc[0,'mob_number']))
        moderator_list = get_moderator_list()
        for i_number in moderator_list:
            send_sms(request_closed_m_sms.format(r_id=r_df.loc[0,'r_id'],r_name=r_df.loc[0,'name'], r_mob_number=r_df.loc[0,'mob_number'],
                                        status=status, v_name=v_df.loc[0,'name'],v_mob_number=v_df.loc[0,'mob_number'],
                                        status_message=status_message),i_number)
        send_sms(request_closed_r_sms.format(status=status),int(r_df.loc[0,'mob_number']))
    if(status == 'cancelled'):
        message_all_volunteers(request_uuid, neighbourhood_radius, search_radius)
    return json.dumps({'Response': {}, 'status': success, 'string_response': response})


@app.route('/admin-update-request', methods=['POST'])
@capture_api_exception
@login_required
def admin_task_completed(*args, **kwargs):
    user_id = kwargs['user_id']
    volunteer_id = request.form.get('volunteer_id')
    request_uuid = request.form.get('request_uuid')
    status = request.form.get('status')
    status_message = request.form.get('status_message', '')
    v_df = volunteer_data_by_id(volunteer_id)
    r_df = request_data_by_uuid(request_uuid)
    user_df = user_data_by_id(user_id)
    if(user_df.shape[0]==0):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'invalid admin user'})
    if status not in ['completed', 'completed externally', 'cancelled', 'reported']:
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'invalid status value'})
    if (status == r_df.loc[0, 'status']):
        return json.dumps({'Response': {}, 'status': False, 'string_response': 'Request Status Already updated'})
    response, success = update_request_status(request_uuid, status, status_message, volunteer_id)
    # Send SMS to Volunteer, Requestor and Moderator - request_closed_v_sms,request_closed_r_sms,request_closed_m_sms
    if ((v_df.shape[0] > 0) & (r_df.shape[0] > 0)):
        send_sms(a_request_closed_v_sms.format(status=status,user_name=user_df.loc[0,'name']), int(v_df.loc[0, 'mob_number']))
        moderator_list = get_moderator_list()
        for i_number in moderator_list:
            send_sms(a_request_closed_m_sms.format(r_id=r_df.loc[0, 'r_id'], r_name=r_df.loc[0, 'name'],
                                                 r_mob_number=r_df.loc[0, 'mob_number'],
                                                 v_name=v_df.loc[0, 'name'],
                                                 v_mob_number=v_df.loc[0, 'mob_number'],status=status, user_name=user_df.loc[0,'name'],
                                                 status_message=status_message), i_number)
        send_sms(a_request_closed_r_sms.format(status=status), int(r_df.loc[0, 'mob_number']))
    if (status == 'cancelled'):
        message_all_volunteers(request_uuid, neighbourhood_radius, search_radius)
    return json.dumps({'Response': {}, 'status': success, 'string_response': response})


@app.route('/messages', methods=['GET'])
@capture_api_exception
@login_required
def get_user_message(*args, **kwargs):
    user_id =  kwargs['user_id']
    df = get_user_messages(user_id)
    if (df.shape[0] > 0):
        return json.dumps(
            {'Response': df.to_dict('records'), 'status': True, 'string_response': 'Request data extracted'},
            default=datetime_converter)
    else:
        return json.dumps({'Response': {}, 'status': True, 'string_response': 'No open requests found'},
                            default=datetime_converter)

# In[ ]:
if(server_type=='local'):
    if __name__ == '__main__':
        app.run(host = os.getenv('HOST') or 'localhost', debug=True,use_reloader=True)
if(server_type=='prod'):
    if __name__ =='__main__':
        app.run()
if (server_type == 'staging'):
    if __name__ == '__main__':
        app.run()

# In[ ]:


# In[ ]:


# In[ ]:
