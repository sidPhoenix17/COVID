#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
from flask import Flask,request,jsonify,json
from flask_cors import CORS
from celery import Celery
import urllib
import uuid
    
from connections import connections

from database_entry import add_requests, add_volunteers_to_db, contact_us_form_add, verify_user,                 add_user, request_matching, check_user, update_requests_db, update_volunteers_db,                 blacklist_token,send_sms, send_otp, resend_otp, verify_otp, update_nearby_volunteers_db, add_request_verification_db

from data_fetching import get_ticker_counts,get_private_map_data,get_public_map_data, get_user_id,                        accept_request_page,request_data_by_uuid,request_data_by_id,volunteer_data_by_id,                        website_requests_display,get_requests_list,website_success_stories, verify_volunteer_exists
from partner_assignment import generate_uuid,message_all_volunteers
from auth import encode_auth_token, decode_auth_token, login_required, volunteer_login_req


from settings import server_type, SECRET_KEY,neighbourhood_radius,moderator_list,search_radius
import cred_config as cc


# In[ ]:


def datetime_converter(o):
    if isinstance(o, dt.datetime):
        return dt.datetime.strftime(o,'%a, %d %b %y, %I:%M%p %Z')


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
    status = request.form.get('status','received')
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
        url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus('Hi')
        sms_text = "[COVIDSOS] "+name+", we have received your request. We will call you soon. If urgent, please click "+url
        send_sms(sms_text,sms_to=int(mob_number),sms_type='transactional',send=True)
#         mod_url = "https://wa.me/91"+str(mob_number)+"?text="+urllib.parse.quote_plus('Hey')
        mod_url = "https://covidsos.org/verify/"+str(uuid)
        mod_sms_text = 'New query received. Verify lead by clicking here: '+mod_url
        for i_number in moderator_list:
            send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
        #move to async
#         volunteer_request.apply_async((latitude,longitude,neighbourhood_radius,search_radius,uuid),countdown=100)
        
        #Move to Async after 5 mins
#         sms_text = "[COVIDSOS] "+name+", you can track your request at "+url
#         send_sms(sms_text,sms_to=int(mob_number),sms_type='transactional',send=True)
        #Send SMS to volunteers via async Task:
        #NEEDS REVIEW
#         volunteer_sms_countdown = 30
#         volunteer_request.apply_async((latitude,longitude,neighbourhood_radius,search_radius,uuid))
#         no_volunteer_assigned.apply_async((latitude,longitude,neighbourhood_radius,search_radius,uuid),countdown=volunteer_sms_countdown)
        #Schedule message after 30 mins depending on status - Send WhatsApp Link here.
    return json.dumps(response)


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


# In[ ]:


@app.route('/login',methods=['POST'])
def login_request():
    name = request.form.get('username')
    password = request.form.get('password')
    response = verify_user(name,password)
    user_id, access_type = get_user_id(name, password)
    if not user_id:
        return {'Response':{},'status':False,'string_response':'Failed to find user.'} 
    response['Response']['auth_token'] = encode_auth_token(f'{user_id} {access_type}').decode()
    return json.dumps(response)


# In[ ]:


@app.route('/new_user',methods=['POST'])
@login_required
def new_user(*args,**kwargs):
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
        user_id, access_type = get_user_id(mob_number, password) 
        if not user_id: 
            return {'Response':{},'status':False,'string_response':'Failed to create user. Please try again later'} 
        response['auth_token'] = encode_auth_token(f'{user_id} {access_type}').decode() 
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


@app.route('/request_status_list',methods=['GET'])
def request_status_list():
    response = get_requests_list()
    return json.dumps({'Response':response,'status':True,'string_respone':'List of Request status'})


# In[ ]:


@app.route('/private_map_data',methods=['GET'])
@login_required
def private_map_data(*args,**kwargs):
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
def assign_volunteer(*args,**kwargs):
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
        if((r_df.loc[0,'status']=='received')or(r_df.loc[0,'status']=='verified')or(r_df.loc[0,'status']=='pending')):
            current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
            req_dict = {'volunteer_id':[v_id],'request_id':[r_df.loc[0,'r_id']],'matching_by':[matching_by],'timestamp':[current_time]}
            df = pd.DataFrame(req_dict)
            response = request_matching(df)
            #Add entry in request_matching table
            response_2 = update_requests_db({'id':r_id},{'status':'matched'})
            response_3 = update_nearby_volunteers_db({'id':r_id},{'status':'expired'})
            #Send to Volunteer
            v_sms_text = '[COVID SOS] Thank you agreeing to help. Name:'+r_df.loc[0,'name']+' Mob:'+str(r_df.loc[0,'mob_number'])+' Request:'+r_df.loc[0,'request']+' Address:'+r_df.loc[0,'geoaddress']
            send_sms(v_sms_text,int(v_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            #Send to Requestor
            v_sms_text = '[COVID SOS] Volunteer '+v_df.loc[0,'name']+' will help you. Mob: '+str(v_df.loc[0,'mob_number'])
            send_sms(v_sms_text,int(r_df.loc[0,'mob_number']),sms_type='transactional',send=True)
        else:
            return json.dumps({'status':False,'string_response':'Request already assigned/closed/completed','Response':{}})
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
        r_id = r_df.loc[0,'r_id']
        if(((r_df.loc[0,'status']=='received')or(r_df.loc[0,'status']=='verified')or(r_df.loc[0,'status']=='pending'))&(task_action=='accepted')):
            current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
            req_dict = {'volunteer_id':[v_id],'request_id':[r_id],'matching_by':[matching_by],'timestamp':[current_time]}
            df = pd.DataFrame(req_dict)
            response = request_matching(df)
            response_2 = update_requests_db({'id':r_id},{'status':'matched'})
            response_3 = update_nearby_volunteers_db({'r_id':r_id},{'status':'expired'})
            #Send to Volunteer
            v_sms_text = '[COVID SOS] Thank you agreeing to help. Name:'+r_df.loc[0,'name']+' Mob:'+str(r_df.loc[0,'mob_number'])+' Request:'+r_df.loc[0,'request']+' Address:'+r_df.loc[0,'geoaddress']
            send_sms(v_sms_text,int(v_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            #Send to Requestor
            v_sms_text = '[COVID SOS] Volunteer '+v_df.loc[0,'name']+' will help you. Mob: '+str(v_df.loc[0,'mob_number'])
            send_sms(v_sms_text,int(r_df.loc[0,'mob_number']),sms_type='transactional',send=True)
            return json.dumps(response)
        elif((r_df.loc[0,'status']=='received')or(r_df.loc[0,'status']=='verified')or(r_df.loc[0,'status']=='pending')):
            response_3 = update_nearby_volunteers_db({'r_id':r_id,'v_id':v_id},{'status':'expired'})
            return json.dumps({'status':True,'string_response':'Request rejected','Response':{}})
        else:
            return json.dumps({'status':False,'string_response':'Request already assigned','Response':{}})


# In[ ]:


@app.route('/update_request_info',methods=['POST'])
@login_required
def update_request_info(*args,**kwargs):
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
    req_dict = {'name':name,'mob_number':mob_number,'email_id':email_id,
                'country':country,'address':address,'geoaddress':geoaddress,'latitude':latitude, 'longitude':longitude,
                'source':source,'age':age,'request':user_request,'status':status}
    if(r_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Request does not exist','Response':{}})
    if (r_id is None):
        return json.dumps({'Response':{},'status':False,'string_response':'Request ID mandatory'})
    r_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_requests_db({'id':r_id},r_dict))
    return response
    


# In[ ]:


# @app.route('/volunteer_api',methods=['GET'])
# @volunteer_login_req
# def volunteer_login_check(*args,**kwargs):
#     print(kwargs['volunteer_id'])
#     return json.dumps({'status':True,'string_response':'Volunteer is logged in','Response':{}})


# In[ ]:


@app.route('/update_volunteer_info',methods=['POST'])
@login_required
def update_volunteer_info(*args,**kwargs):
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
    req_dict = {'name':name,'mob_number':mob_number,'email_id':email_id,
                'country':country,'address':address,'geoaddress':geoaddress,'latitude':latitude, 'longitude':longitude,
                'source':source,'status':status}
    v_df = volunteer_data_by_id(v_id)
    if(v_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Volunteer does not exist','Response':{}})
    if (v_id is None):
        return {'Response':{},'status':False,'string_response':'Volunteer ID mandatory'}
    v_dict = {x:req_dict[x] for x in req_dict if req_dict[x] is not None}
    response = json.dumps(update_volunteers_db({'id':v_id},v_dict))
    return response


# In[ ]:


@app.route('/logout',methods=['POST'])
@login_required
def logout_request(*args,**kwargs):
    token = request.headers['Authorization'].split(" ")[1]
    success = blacklist_token(token)
    message = 'Logged out successfully' if success else 'Failed to logout'
    return json.dumps({'Response': {}, 'status': success, 'string_response': message}) 


# In[ ]:


@app.route('/accept_page',methods=['POST'])
#Volunteer Login Required
def request_accept_page():
    uuid = request.form.get('uuid')
    #Can be removed once authentication is implemented
    v_mob_number = request.form.get('mob_number')
    df = accept_request_page(uuid)
    if(df.shape[0]==0):
        return json.dumps({'Response':{},'status':False,'string_response':'This page does not exist. Redirecting to homepage'})
    else:
        if(df.loc[0,'status'].isin(['received','verified','pending'])):
            return json.dumps({'Response':df.to_dict('records'),'status':True,'string_response':'Request related data extracted'})
        else:
            return json.dumps({'Response':{},'status':False,'string_response':'This request is already completed'})


# In[ ]:


@app.route('/verify_request_page',methods=['POST'])
@login_required
def verify_request_page(*args,**kwargs):
    uuid = request.form.get('uuid')
    r_df = request_data_by_uuid(uuid)
    if(r_df.shape[0]==0):
        return json.dumps({'status':False,'string_response':'Request ID does not exist.','Response':{}})
    if(r_df.loc[0,'status']=='received'):
        return json.dumps({'Response':r_df.to_dict('records'),'status':True,'string_response':'Request data extracted'},default=datetime_converter)
    else:
        return json.dumps({'Response':{},'status':False,'string_response':'Request already verified/rejected'})


# In[ ]:


@app.route('/verify_request',methods=['POST'])
@login_required
def verify_request(*args,**kwargs):
    uuid = request.form.get('uuid')
    what = request.form.get('what')
    why = request.form.get('why')
    verification_status=request.form.get('verification_status')
    verified_by = kwargs.get('user_id',0)
# request.form.get('verified_by',331)
#     if(str(verified_by).isdigit()):
#         verified_by=int(verified_by)
#     else:
#         verified_by=0
    r_id = request.form.get('r_id')
    name = request.form.get('name')
    where = request.form.get('geoaddress')
    mob_number = request.form.get('mob_number')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    if(verification_status is None):
        return json.dumps({'Response':{},'status':False,'string_response':'Please send verification status'})
    if((r_id is None) or (uuid is None)):
        return json.dumps({'Response':{},'status':False,'string_response':'Please send UUID/request ID'})
    r_df = request_data_by_uuid(uuid)
    if(r_df.shape[0]==0):
        return json.dumps({'Response':{},'status':False,'string_response':'Invalid UUID/request ID'})
    if(r_df.loc[0,'status']=='received'):
        r_v_dict = {'r_id':[r_id],'why':[why],'what':[what],'where':[where],'verification_status':[verification_status],'verified_by':[verified_by],'timestamp':[current_time]}
        df = pd.DataFrame(r_v_dict)
        expected_columns=['timestamp', 'r_id','what', 'why', 'where', 'verification_status','verified_by']
        response_2 = update_requests_db({'uuid':uuid},{'status':verification_status})
        print('updated the status')
        x,y = add_request_verification_db(df)
        if(verification_status=='verified'):
            requestor_text = '[COVIDSOS] Your request has been verified. We will look for volunteers in your neighbourhood.'
            send_sms(requestor_text,sms_to=int(mob_number),sms_type='transactional',send=True)
            message_all_volunteers(uuid,neighbourhood_radius,search_radius)
        else:
            requestor_text = '[COVIDSOS] Your request has been cancelled/rejected. If you still need help, please submit request again.'
            send_sms(requestor_text,sms_to=int(mob_number),sms_type='transactional',send=True)
        return json.dumps({'Response':{},'status':response_2['status'],'string_response':response_2['string_response']})
    else:
        return json.dumps({'Response':{},'status':False,'string_response':'Request already verified/rejected'})


# In[ ]:


@app.route('/pending_requests',methods=['GET'])
def pending_requests():
    response = website_requests_display()
    return json.dumps({'Response':response,'status':True,'string_response':'Request data extracted'})


# In[ ]:


@app.route('/success_stories',methods=['GET'])
def success_stories():
    response = website_success_stories()
    return json.dumps({'Response':response,'status':True,'string_response':'Success stories data extracted'})


# In[ ]:



@app.route('/request_otp', methods=['POST'])
def send_otp_request():
    mob_number = request.form.get('mob_number')
    if not verify_volunteer_exists(mob_number)['status']:
        return json.dumps({'Response':{},'status':False,'string_response':'No user found for this mobile number'})
    response, success = send_otp(mob_number)
    return json.dumps({'Response':{},'status':success,'string_response':response})


@app.route('/resend_otp',methods=['POST'])
def resend_otp_request():
    mob_number = request.form.get('mob_number')
    if not verify_volunteer_exists(mob_number)['status']:
        return json.dumps({'Response':{},'status':False,'string_response':'No user found for this mobile number'})
    response, success = resend_otp(mob_number)
    return json.dumps({'Response':{},'status':success,'string_response':response})

@app.route('/verify_otp',methods=['POST'])
def verify_otp_request():
    mob_number = request.form.get('mob_number')
    otp = request.form.get('otp')
    userData = verify_volunteer_exists(mob_number)
    if not userData['status']:
        return json.dumps({'Response':{},'status':False,'string_response':'No user found for this mobile number'})
    response, success = verify_otp(otp, mob_number)
    responseObj = {}
    if success:
        user_id = userData['volunteer_id']
        country = userData['country']
        encodeKey = f'{user_id} {country}'
        responseObj = {'auth_token': encode_auth_token(encodeKey).decode()}
    return json.dumps({'Response':responseObj,'status':success,'string_response':response})


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




