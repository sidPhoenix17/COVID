#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import datetime as dt
from flask import Flask,request,jsonify,json
from flask_cors import CORS

from connections import connections
from database_entry import add_requests,add_volunteers_to_db,contact_us_form_add,verify_user,add_user,request_matching,request_updation,volunteer_updation,check_user

from data_fetching import get_ticker_counts,get_private_map_data,get_public_map_data
from settings import *


# In[ ]:


app = Flask(__name__)
CORS(app)


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
    age = request.form.get('age')
    address = request.form.get('address')
    user_request = request.form.get('request')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[''],
                'country':['India'],'address':[address],'geoaddress':[address],'latitude':[latitude], 'longitude':[longitude],
                'source':['website'],'age':[age],'request':[user_request]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']
    x,y = add_requests(df)
    response = {'status':x,'string_response':y}
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/create_volunteer',methods=['POST'])
def add_volunteer():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':email_id,
                'country':['India'],'address':[address],'geoaddress':[address],'latitude':[latitude], 'longitude':[longitude],
                'source':['website']}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source']
    x,y = add_volunteers_to_db(df)
    response = {'status':x,'string_response':y}
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/login',methods=['POST'])
def login_request():
    name = request.form.get('username')
    password = request.form.get('password')
#     req_dict = {'username':name,'password':password}
#     df = pd.DataFrame(req_dict)
    response = verify_user(name,password)
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/new_user',methods=['POST'])
def new_user():
    name = request.form.get('name')
    mob_number = request.form.get('mob_number')
    email_id = request.form.get('email_id')
    password = request.form.get('password')
    organisation = request.form.get('organisation')
    creator_access_type = request.form.get('creator_access_type')
    user_access_type = request.form.get('user_access_type')
    creator_user_id = request.form.get('creator_user_id')
    print(user_access_type)
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    if(user_access_type=='moderator'):
        access_type=2
    elif(user_access_type=='viewer'):
        access_type=3    
    elif(user_access_type=='superuser'):
        response = {'status':False,'string_response':'You cannot create superuser'}
        return jsonify(Response=response)
    else:
        response = {'status':False,'string_response':'Invalid access type'}
        return jsonify(Response=response)
    req_dict = {'creation_date':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[email_id],'organisation':[organisation],'password':[password],'access_type':[user_access_type],'created_by':creator_user_id}
    df = pd.DataFrame(req_dict)
    if(creator_access_type=='superuser'):
        response = add_user(df)
    else:
        response = {'status':False,'string_response':'User does not have permission to create new users'}
    return json.dumps({'Response':response})


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
    response = {'status':x,'string_response':y}
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/top_ticker',methods=['POST'])
def ticker_counts():
    response = get_ticker_counts()
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/private_map_data',methods=['POST'])
def private_map_data():
    user_id = request.form.get('user_id')
#     req_dict = {'username':name,'password':password}
#     df = pd.DataFrame(req_dict)
    response = check_user('users',user_id)    
    if(response['status']):
        response = get_private_map_data()
    return json.dumps({'Response':response,'status':True,'string_response':'Full data sent'})


# In[ ]:


@app.route('/public_map_data',methods=['POST'])
def public_map_data():
    response = get_public_map_data()
    return json.dumps({'Response':response,'status':True,'string_response':'Public data sent'})


# In[ ]:


@app.route('/assign_volunteer',methods=['POST'])
def assign_volunteer():
    v_id = request.form.get('volunteer_id')
    r_id = request.form.get('request_id')
    matching_by = request.form.get('matched_by')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'volunteer_id':[v_id],'request_id':[r_id],'matching_by':[matching_by],'timestamp':[current_time]}
    df = pd.DataFrame(req_dict)
    response = request_matching(df)
    response_2 = request_updation(r_id,'status','matched',current_time)
    return json.dumps({'Response':response})


# In[ ]:


@app.route('/update_request',methods=['POST'])
def update_request():
    r_id = request.form.get('request_id')
    column_name = request.form.get('column_name')
    new_value = request.form.get('new_value')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    response = request_updation(r_id,column_name,new_value,current_time)
    return response


# In[ ]:


@app.route('/inactivate_volunteer',methods=['POST'])
def volunteer_activation():
    v_id = request.form.get('volunteer_id')
    column_name = request.form.get('column_name')
    new_value = request.form.get('new_value')
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    response = volunteer_updation(v_id,column_name,new_value,current_time)
    return response


# In[ ]:





# In[ ]:


# from folium import Map, Marker, GeoJson
# from folium.plugins import MarkerCluster


# @app.route('/folium_test',methods=['POST'])
# def folium_test_fn():
#     v_df, r_df = folium_data_request()
#     m = Map(location= [12.97194, 77.59369], zoom_start= 12, tiles="cartodbpositron", 
#             attr= '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="http://cartodb.com/attributions#basemaps">CartoDB</a>')
#     volunteer_cluster = MarkerCluster()
#     for i in v_df.index:
#         mk = Marker(location=[v_df.loc[i,'latitude'],v_df.loc[i,'longitude']])
#         mk.add_to(volunteer_cluster)
#     volunteer_cluster.add_to(m)
#     requests_cluster = MarkerCluster()
#     for i in r_df.index:
#         mk = Marker(location=[r_df.loc[i,'latitude'],r_df.loc[i,'longitude']])
#         mk.add_to(requests_cluster)
#     requests_cluster.add_to(m)
#     m.save('output/folium_test.html')
#     return m._repr_html_()


# In[ ]:


if(server_type=='local'):
    if __name__ == '__main__':    
        app.run(debug=True,use_reloader=False)

if(server_type=='server'):
    if __name__ =='__main__':
        app.run()


# In[ ]:




