#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
from flask import Flask,request,jsonify,json
from flask_cors import CORS

from connections import connections
from database_entry import add_requests, add_volunteers_to_db, contact_us_form_add, verify_user, add_user, request_matching, check_user, update_requests_db, update_volunteers_db, blacklist_token

from data_fetching import get_ticker_counts,get_private_map_data,get_public_map_data, get_user_id
from settings import server_type, SECRET_KEY
from auth import encode_auth_token, decode_auth_token, login_required

from celery import Celery


# In[ ]:


def datetime_converter(o):
    if isinstance(o, dt.datetime):
        return dt.datetime.strftime(o,'%a, %d %b %y, %I:%M%p %Z')


# In[ ]:


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = SECRET_KEY


# In[ ]:



app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def async_task():
    print("1234")
    print(dt.datetime.now())

    

@app.route('/test_async',methods=['GET'])
def test_async():
    try:
        async_task.delay()
    except Exception as e:
        response = {'Response':str(e),'status':200,'string_response':'Ok'}
        return json.dumps(response)
    response = {'Response':{'key': 'Ok'},'status':200,'string_response':'Ok'}
    return json.dumps(response)


# In[ ]:


# 1. request help
# 2. volunteer register
# 3. org register
# 4. login
# 5. user register (by you)
#To Do
# 6. get map data - open
# 7. get map data - authorised, all details
# 8. assign user


# In[ ]:


@app.route('/create_request',methods=['POST'])
def create_request():
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
    status = request.form.get('status')
    country = request.form.get('country')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],
                'country':[country],'address':[address],'geoaddress':[geoaddress],'latitude':[latitude], 'longitude':[longitude],
                'source':[source],'age':[age],'request':[user_request],'status':[status]}
    df = pd.DataFrame(req_dict)
    df['source'] = df['source'].fillna('covidsos')
    df['status'] = df['status'].fillna('pending')
    df['email_id'] = df['email_id'].fillna('')
    df['latitude'] = df['latitude'].fillna(0.0)
    df['longitude'] = df['longitude'].fillna(0.0)
    df['country'] = df['country'].fillna('India')
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age','status']
    x,y = add_requests(df)
    response = {'Response':{},'status':x,'string_response':y}
    return json.dumps(response)


# In[ ]:


@app.route('/create_volunteer',methods=['POST'])
def add_volunteer():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    source = request.form.get('source')
    status = request.form.get('status')
    country = request.form.get('country')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],
                'country':[country],'address':[address],'geoaddress':[geoaddress],'latitude':[latitude], 'longitude':[longitude],
                'source':[source],'status':[status]}
    df = pd.DataFrame(req_dict)
    df['status'] = df['status'].fillna(1)
    df['country'] = df['country'].fillna('India')
    df['latitude'] = df['latitude'].fillna(0.0)
    df['longitude'] = df['longitude'].fillna(0.0)
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source','status']
    x,y = add_volunteers_to_db(df)
    response = {'Response':{},'status':x,'string_response':y}
    return json.dumps(response)


# In[ ]:


@app.route('/login',methods=['POST'])
def login_request():
    name = request.form.get('username')
    password = request.form.get('password')
    response = verify_user(name,password)
    user_id = get_user_id(name, password) 
    if not user_id: 
        return {'Response':{},'status':False,'string_response':'Failed to find user.'} 
    response['Response']['auth_token'] = encode_auth_token(user_id).decode()
    return json.dumps(response)


# In[ ]:


@app.route('/new_user',methods=['POST'])
@login_required
def new_user():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    password = request.form.get('password')
    organisation = request.form.get('organisation')
    creator_access_type = request.form.get('creator_access_type')
    user_access_type = request.form.get('user_access_type')
    creator_user_id = request.form.get('creator_user_id')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    if(user_access_type=='moderator'):
        access_type=2
    elif(user_access_type=='viewer'):
        access_type=3    
    elif(user_access_type=='superuser'):
        response = {'Response':{},'status':False,'string_response':'You cannot create superuser'}
        return json.dumps(response)
    else:
        response = {'Response':{},'status':False,'string_response':'Invalid access type'}
        return json.dumps(response)
    req_dict = {'creation_date':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],'organisation':[organisation],'password':[password],'access_type':[access_type],'created_by':creator_user_id}
    df = pd.DataFrame(req_dict)
    if(creator_access_type=='superuser'):
        response = add_user(df)
        user_id = get_user_id(mob_number, password) 
        if not user_id: 
            return {'Response':{},'status':False,'string_response':'Failed to create user. Please try again later'} 
        response['auth_token'] = encode_auth_token(user_id).decode() 
    else:
        response = {'Response':{},'status':False,'string_response':'User does not have permission to create new users'}
    return json.dumps(response)


# In[ ]:


@app.route('/reachout_form',methods=['POST'])
def add_org_request():
    name = request.form.get('name')
    organisation = request.form.get('organisation')
    email_id = request.form.get('email_id')
    mob_number = request.form.get('mob_number')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    comments = request.form.get('comments')
    req_dict = {'timestamp':[current_time],'name':[name],'organisation':[organisation],'mob_number':[mob_number],'email_id':[email_id],
                'source':['website'],'comments':[comments]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name','organisation','mob_number','email_id', 'source','comments']
    x,y = contact_us_form_add(df)
    response = {'Response':{},'status':x,'string_response':y}
    return json.dumps(response)


# In[ ]:


@app.route('/top_ticker',methods=['GET'])
def ticker_counts():
    response = get_ticker_counts()
    return json.dumps(response)


# In[ ]:


@app.route('/private_map_data',methods=['GET'])
@login_required
def private_map_data():
    response = get_private_map_data() 
    return json.dumps({'Response':response,'status':True,'string_response':'Full data sent'},default=datetime_converter)


# In[ ]:


@app.route('/public_map_data',methods=['GET'])
def public_map_data():
    response = get_public_map_data()
    return json.dumps({'Response':response,'status':True,'string_response':'Public data sent'})


# In[ ]:


@app.route('/assign_volunteer',methods=['POST'])
@login_required
def assign_volunteer():
    v_id = request.form.get('volunteer_id')
    r_id = request.form.get('request_id')
    matching_by = request.form.get('matched_by')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'volunteer_id':[v_id],'request_id':[r_id],'matching_by':[matching_by],'timestamp':[current_time]}
    df = pd.DataFrame(req_dict)
    response = request_matching(df)
    response_2 = update_requests_db({'id':r_id,'status':'matched'})
    return json.dumps(response)


# In[ ]:


@app.route('/update_request_info',methods=['POST'])
@login_required
def update_request_info():
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
    status = request.form.get('status')
    country = request.form.get('country')
    req_dict = {'id':r_id,'name':name,'mob_number':mob_number,'email_id':email_id,
                'country':country,'address':address,'geoaddress':geoaddress,'latitude':latitude, 'longitude':longitude,
                'source':source,'age':age,'request':user_request,'status':status}
    if (req_dict.get('id') is None):
        return json.dumps({'Response':{},'status':False,'string_response':'Request ID mandatory'})
    r_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = update_requests_db(r_dict)
    return response
    


# In[ ]:


@app.route('/update_volunteer_info',methods=['POST'])
@login_required
def update_volunteer_info():
    v_id = request.form.get('volunteer_id')
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    source = request.form.get('source')
    status = request.form.get('status')
    country = request.form.get('country')
    req_dict = {'id':v_id,'name':name,'mob_number':mob_number,'email_id':email_id,
                'country':country,'address':address,'geoaddress':geoaddress,'latitude':latitude, 'longitude':longitude,
                'source':source,'status':status}
    if (req_dict.get('id') is None):
        return {'Response':{},'status':False,'string_response':'Volunteer ID mandatory'}
    v_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = update_volunteers_db(v_dict)
    return response


# In[ ]:


@app.route('/logout',methods=['POST'])
@login_required
def logout_request():
    token = request.headers['Authorization'].split(" ")[1]
    success = blacklist_token(token)
    message = 'Logged out successfully' if success else 'Failed to logout'
    return json.dumps({'Response': {}, 'status': success, 'string_response': message}) 


# In[ ]:


if(server_type=='local'):
    if __name__ == '__main__':    
        app.run(debug=True,use_reloader=False)

if(server_type=='prod'):
    if __name__ =='__main__':
        app.run()
if(server_type=='staging'):
    if __name__ =='__main__':
        app.run()


# In[ ]:




