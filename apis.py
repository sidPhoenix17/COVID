#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
# import json
from flask import Flask,request,jsonify,json
from flask_cors import CORS

from connections import connections
from database_entry import add_requests,add_volunteers_to_db,contact_us_form_add

from settings import *


# In[ ]:


app = Flask(__name__)
CORS(app)


# In[ ]:


# 1. request help
# 2. volunteer register
# 3. org register
#To Do
# 4. login
# 5. user register (by you)
# 6. get map data - open
# 7. get map data - authorised, all details
# 8. assign user


# In[ ]:


@app.route('/create_request',methods=['POST'])
def create_request():
    name = request.args['name']
    mob_number = request.args['mob_number']
    age = request.args['age']
    address = request.args['address']
    user_request = request.args['request']
    latitude = request.args['latitude']
    longitude = request.args['longitude']
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[''],
                'country':['India'],'address':[address],'geoaddress':[address],'latitude':[latitude], 'longitude':[longitude],
                'source':['website'],'age':[age],'request':[user_request]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']
    x,y = add_requests(df)
    response = {'status':x,'output':y}
    return jsonify(Response=response)


# In[ ]:


@app.route('/create_volunteer',methods=['POST'])
def add_volunteer():
    name = request.args['name']
    mob_number = request.args['mob_number']
    email_id = request.args['email_id']
    address = request.args['address']
    latitude = request.args['latitude']
    longitude = request.args['longitude']
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':email_id,
                'country':['India'],'address':[address],'geoaddress':[address],'latitude':[latitude], 'longitude':[longitude],
                'source':['website']}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source']
    x,y = add_volunteers_to_db(df)
    response = {'status':x,'output':y}
    return jsonify(Response = response)


# In[ ]:


@app.route('/reachout_form',methods=['POST'])
def add_org_request():
    name = request.args['name']
    organisation = request.args['organisation']
    email_id = request.args['email_id']
    mob_number = request.args['mob_number']
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    comments = request.args['comments']
    req_dict = {'timestamp':[current_time],'name':[name],'organisation':[organisation],'mob_number':[mob_number],'email_id':email_id,
                'source':['website'],'comments':[comments]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name','organisation','mob_number','email_id', 'source','comments']
    x,y = contact_us_form_add(df)
    response = {'status':x,'output':y}
    return jsonify(Response = response)


# In[ ]:


if(server_type=='local'):
    if __name__ == '__main__':    
        app.run(debug=True,use_reloader=False)

if(server_type=='server'):
    if __name__ =='__main__':
        app.run()


# In[ ]:





# In[ ]:




