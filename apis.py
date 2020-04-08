#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
from flask import Flask,request,jsonify,json
from flask_cors import CORS

from connections import connections
from database_entry import add_requests, add_volunteers_to_db, contact_us_form_add, verify_user,                 add_user, request_matching, check_user, update_requests_db, update_volunteers_db,                 blacklist_token,send_sms,update_nearby_volunteers_db

from data_fetching import get_ticker_counts,get_private_map_data,get_public_map_data, get_user_id,                        accept_request_page,request_data_by_uuid,request_data_by_id,volunteer_data_by_id,website_requests_display
from settings import server_type, SECRET_KEY,neighbourhood_radius,moderator_list,search_radius
from auth import encode_auth_token, decode_auth_token, login_required

import uuid
from partner_assignment import generate_uuid
from celery import Celery
import urllib


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


@celery.task
def volunteer_request(lat,lon,radius,uuid):
    print('Running volunteer_request function at ', dt.datetime.now())
    message_all_volunteers(lat,lon,radius,search_radius,uuid)
    return None


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


@app.route('/create_request',methods=['POST'])
def create_request():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id','')
    age = request.form.get('age')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    user_request = request.form.get('request')
    latitude = request.form.get('latitude',0.0)
    longitude = request.form.get('longitude',0.0)
    source = request.form.get('source','covidsos')
    status = request.form.get('status','pending')
    country = request.form.get('country','India')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    uuid = generate_uuid()
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],
                'country':[country],'address':[address],'geoaddress':[geoaddress],'latitude':[latitude], 'longitude':[longitude],
                'source':[source],'age':[age],'request':[user_request],'status':[status],'uuid':[uuid]}
    df = pd.DataFrame(req_dict)
    df['email_id'] = df['email_id'].fillna('')
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age','status','uuid']
    x,y = add_requests(df)
    response = {'Response':{},'status':x,'string_response':y}
    if(x):
#         url = "https://covidsos.org/track/{uuid}".format(uuid=uuid)
        url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus('Hi')
        sms_text = "[COVIDSOS] "+name+", we are contacting our volunteers for support. If urgent, please click "+url
        send_sms(sms_text,sms_to=int(mob_number),sms_type='transactional',send=True)
        mod_url = "https://wa.me/91"+str(mob_number)+"?text="+urllib.parse.quote_plus('Hey')
        mod_sms_text = 'New query received. '+mod_url
        for i_number in moderator_list:
            send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
        #move to async
        volunteer_request(latitude,longitude,neighbourhood_radius,search_radius,uuid)
#         volunteer_request.apply_async((latitude,longitude,neighbourhood_radius,search_radius,uuid),countdown=100)
        
        #Move to Async after 5 mins
#         sms_text = "[COVIDSOS] "+name+", you can track your request at "+url
#         send_sms(sms_text,sms_to=int(mob_number),sms_type='transactional',send=True)
        #Send SMS to volunteers via async Task:
        #NEEDS REVIEW
#         volunteer_sms_countdown = 30
#         volunteer_request.apply_async((latitude,longitude,neighbourhood_radius,uuid))
#         no_volunteer_assigned.apply_async((latitude,longitude,neighbourhood_radius,uuid),countdown=volunteer_sms_countdown)
        #Schedule message after 30 mins depending on status - Send WhatsApp Link here.
    return json.dumps(response)

#     df['source'] = df['source'].fillna('covidsos')
#     df['status'] = df['status'].fillna('pending')
#     df['latitude'] = df['latitude'].fillna(0.0)
#     df['longitude'] = df['longitude'].fillna(0.0)
#     df['country'] = df['country'].fillna('India')


# In[ ]:


@app.route('/create_volunteer',methods=['POST'])
def add_volunteer():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id','')
    address = request.form.get('address')
    geoaddress = request.form.get('geoaddress', address)
    latitude = request.form.get('latitude',0.0)
    longitude = request.form.get('longitude',0.0)
    source = request.form.get('source')
    status = request.form.get('status',1)
    country = request.form.get('country','India')
    support_type = request.form.get('support_type','Deliver groceries and/or medicines')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],
                'country':[country],'address':[address],'geoaddress':[geoaddress],'latitude':[latitude], 'longitude':[longitude],
                'source':[source],'status':[status],'support_type':[support_type]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source','status','support_type']
    x,y = add_volunteers_to_db(df)
    if(x):
        url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("Hi")
        if(y=='Volunteer already exists. No New Volunteers to be added'):
            sms_text = "[COVIDSOS] You are already registered with us. Click here to contact us "+url
        else:    
            sms_text = "[COVIDSOS] Thank you for registering. Click here to contact us:"+url
        send_sms(sms_text,sms_to=int(mob_number),sms_type='transactional',send=True)
    response = {'Response':{},'status':x,'string_response':y}
    return json.dumps(response)

#     df['status'] = df['status'].fillna(1)
#     df['country'] = df['country'].fillna('India')
#     df['latitude'] = df['latitude'].fillna(0.0)
#     df['longitude'] = df['longitude'].fillna(0.0)


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
    req_dict = {'creation_date':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],'organisation':[organisation],'password':[password],'access_type':[access_type],'created_by':[creator_user_id]}
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
    r_df = request_data_by_id(r_id)
    v_df = volunteer_data_by_id(v_id)
    if(r_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Request ID does not exist.','Response':{}})
    if(v_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Volunteer does not exist','Response':{}})
    else:
        if(r_df.loc[0,'status']=='pending'):
            current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
            req_dict = {'volunteer_id':[v_id],'request_id':[r_df.loc[0,'r_id']],'matching_by':[matching_by],'timestamp':[current_time]}
            df = pd.DataFrame(req_dict)
            response = request_matching(df)
            #Add entry in request_matching table
            response_2 = update_requests_db({'id':r_id,'status':'matched'})
            response_3 = update_nearby_volunteers_db({'id':r_id},{'status':'expired'})
            #Send to Volunteer
            v_sms_text = '[COVID SOS] Thank you agreeing to help. Name:'+r_df.loc[0,'name']+' Mob:'+str(r_df.loc[0,'mob_number'])+' Request:'+r_df.loc[0,'request']+' Address:'+r_df.loc[0,'geoaddress']
            send_sms(v_sms_text,int(v_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            #Send to Requestor
            v_sms_text = '[COVID SOS] Volunteer '+v_df.loc[0,'name']+' will help you. Mob: '+str(v_df.loc[0,'mob_number'])
            send_sms(v_sms_text,int(r_df.loc[0,'mob_number']),sms_type='transactional',send=True)
        else:
            return json.dumps({'status':False,'string_response':'Request already assigned','Response':{}})
    return json.dumps(response)


# In[ ]:


@app.route('/auto_assign_volunteer',methods=['POST'])
def auto_assign_volunteer():
    v_id = request.form.get('volunteer_id')
    uuid = request.form.get('uuid')
    matching_by = 'autoassigned'
    task_action = request.form.get('task_action')
    r_df = request_data_by_uuid(uuid)
    v_df = volunteer_data_by_id(v_id)
    if(r_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Request ID does not exist.','Response':{}})
    if(v_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Volunteer does not exist','Response':{}})
    else:
        if((r_df.loc[0,'status']=='pending')&(task_action=='accepted')):
            current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
            req_dict = {'volunteer_id':[v_id],'request_id':[r_df.loc[0,'r_id']],'matching_by':[matching_by],'timestamp':[current_time]}
            df = pd.DataFrame(req_dict)
            response = request_matching(df)
            response_2 = update_requests_db({'id':r_df.loc[0,'r_id'],'status':'matched'})
            response_3 = update_nearby_volunteers_db({'r_id':r_df.loc[0,'r_id']},{'status':'expired'})
            #Send to Volunteer
            v_sms_text = '[COVID SOS] Thank you agreeing to help. Name:'+r_df.loc[0,'name']+' Mob:'+str(r_df.loc[0,'mob_number'])+' Request:'+r_df.loc[0,'request']+' Address:'+r_df.loc[0,'geoaddress']
            send_sms(v_sms_text,int(v_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            #Send to Requestor
            v_sms_text = '[COVID SOS] Volunteer '+v_df.loc[0,'name']+' will help you. Mob: '+str(v_df.loc[0,'mob_number'])
            send_sms(v_sms_text,int(r_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            return json.dumps(response)
        elif(r_df.loc[0,'status']=='pending'):
            response_3 = update_nearby_volunteers_db({'r_id':r_id,'v_id':v_id},{'status':'expired'})            
        else:
            return json.dumps({'status':False,'string_response':'Request already assigned','Response':{}})


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
    r_df = request_data_by_id(r_id)
    if(r_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Request ID does not exist.','Response':{}})
    req_dict = {'id':r_id,'name':name,'mob_number':mob_number,'email_id':email_id,
                'country':country,'address':address,'geoaddress':geoaddress,'latitude':latitude, 'longitude':longitude,
                'source':source,'age':age,'request':user_request,'status':status}
    if (req_dict.get('id') is None):
        return json.dumps({'Response':{},'status':False,'string_response':'Request ID mandatory'})
    r_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_requests_db(r_dict))
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
    v_df = volunteer_data_by_id(v_id)
    if(v_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Volunteer does not exist','Response':{}})
    if (req_dict.get('id') is None):
        return {'Response':{},'status':False,'string_response':'Volunteer ID mandatory'}
    v_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_volunteers_db(v_dict))
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


@app.route('/accept_page',methods=['POST'])
def request_accept_page():
    uuid = request.form.get('uuid')
    v_mob_number = request.form.get('mob_number')
    df = accept_request_page(uuid,v_mob_number)
    if(df.shape[0]==0):
        return json.dumps({'Response':{},'status':False,'string_response':'This page does not exist. Redirecting to homepage'})
    else:
        if(df.loc[0,'status']=='pending'):
            return json.dumps({'Response':df.to_dict('records'),'status':True,'string_response':'Request related data extracted'})
        else:
            return json.dumps({'Response':{},'status':False,'string_response':'This request is already completed'})


# In[ ]:


@app.route('/pending_requests',methods=['GET'])
def pending_requests():
    response = website_requests_display()
    return json.dumps({'Response':response,'status':True,'string_response':'Request data extracted'})


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





# In[ ]:





# In[ ]:




