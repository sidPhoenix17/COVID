#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
from connections import connections,keys
import requests
from sqlalchemy.sql import text
import datetime as dt


# In[ ]:


#todo - AddUser
#Check if User Exists
#password encryption


# In[ ]:


def remove_existing_volunteers(df):
    server_con = connections('db_read')
    query = """Select mob_number from volunteers"""
    volunteer_list = pd.read_sql(query,server_con)
    df['mob_number']=df['mob_number'].apply(lambda x: int(x))
    df_new = df[df['mob_number'].isin(volunteer_list['mob_number'].unique())==False]
    return df_new
    
def last_entry_timestamp(source):
    server_con = connections('db_read')
    query = """Select max(timestamp) as timestamp from requests where source='{source}'""".format(source=source)
    max_timestamp = pd.read_sql(query,server_con,parse_dates=['timestamp'])    
    max_timestamp['source']=source
    return max_timestamp


# In[ ]:



def add_volunteers_to_db(df_full):
    df = remove_existing_volunteers(df_full)
    df['timestamp']=pd.to_datetime(df['timestamp'])
    if(df.shape[0]>0):
        print(df.shape[0], ' New volunteers to be added')
    else:
        return_str = 'Volunteer already exists. No New Volunteers to be added'
        return True, return_str
    #df with columns [timestamp, name, mob_number, email_id, country, address, geoaddress,latitude, longitude, source]
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('db_write')
        df.to_sql(name = 'volunteers', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Volunteer Data Submitted'
        return True,return_str
    else:
        return_str = 'Data format not matching'
        return False,return_str

def add_requests(df):
    #df with columns [timestamp, name,mob_number, email_id, country, address, geoaddress, latitude, longitude, source, request,age]
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('db_write')
        df.to_sql(name = 'requests', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Request submitted successfully'
        return True,return_str
    else:
        return_str = 'Data Format not matching'
        return False,return_str

def contact_us_form_add(df):
    expected_columns=['timestamp', 'name','organisation', 'mob_number', 'email_id', 'comments','source']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('db_write')
        df.to_sql(name = 'org_requests', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Request submitted successfully'
        return True,return_str
    else:
        return_str = 'Data Format not matching'
        return False,return_str


# In[ ]:



def geocoding(address_str,country_str,key):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+str(address_str)+'&components=country:'+str(country_str)+'&key='+key
    try:
        r = requests.get(url=url)
        data = r.json()
        if data["status"]=="OK":
            return (data['results'][0]['geometry']['location']['lng'], 
                    data['results'][0]['geometry']['location']['lat'])
        else:
            print(data["status"] + " for "+ address_str)
            return None
    except:
        print("HTTP Error for "+address_str)
        return None


# In[ ]:





# In[ ]:



def verify_user(username,password):
    server_con = connections('db_read')
    query = """Select users.id as id,name as full_name, mob_number,email_id,password,user_access.type as type from users left join user_access on users.access_type=user_access.id"""
    user_list = pd.read_sql(query,server_con)
    for i in user_list.index:
        if(((str(user_list.loc[i,'mob_number'])==username) or (user_list.loc[i,'email_id']==username)) and (user_list.loc[i,'password']==password)):
            return {'string_response': 'Login successful','access_level': user_list.loc[i,'type'],'status':True,'username':username,'user_id':str(user_list.loc[i,'id']),'full_name':user_list.loc[i,'full_name']}
        elif(((str(user_list.loc[i,'mob_number'])==username) or (user_list.loc[i,'email_id']==username)) and (user_list.loc[i,'password']!=password)):
            return {'string_response': 'Incorrect Password','access_level': '','status':False,'username':username}
        else:
            return {'string_response': 'Incorrect Username','access_level':'','status':False,'username':username}


# In[ ]:



def add_user(df):
    expected_columns=['creation_date', 'name', 'mob_number', 'email_id', 'organisation', 'password', 'access_type','created_by']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('db_write')
        df.to_sql(name = 'users', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return  {'string_response': 'User Added Successfully','status':True}
    else:
        return  {'string_response': 'User addition failed due to incorrect data format' ,'status':False}
    


# In[ ]:



def request_matching(df):
    expected_columns=['request_id','volunteer_id','matching_by','timestamp']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('db_write')
        df.to_sql(name = 'request_matching', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return  {'string_response': 'Volunteer Assigned','status':True}
    else:
        return  {'string_response': 'Volunteer assignment failed due to incorrect data format' ,'status':False}
        


# In[ ]:


def request_updation(r_id,column,new_value,timestamp):
    engine = connections('db_write')
    try:
        with engine.connect() as con:
            query = text("""update requests set {column_name}='{new_value}',last_updated='{timestamp}' 
            where id={r_id};""".format(column_name=column,new_value=new_value, timestamp =dt.datetime.strftime(timestamp,'%Y-%m-%d %H:%M:%S'),r_id=r_id))
            con.execute(query)
            return {'string_response': 'Request Updated','status':True}
    except e:
        return  {'string_response': 'Volunteer updation failed' ,'status':False}


# In[ ]:


def volunteer_updation(v_id,column,new_value,timestamp):
    engine = connections('db_write')
    try:
        with engine.connect() as con:
            query = text("""update volunteers set {column_name}='{new_value}',last_updated='{timestamp}' 
            where id={v_id};""".format(column_name=column,new_value=new_value, timestamp =dt.datetime.strftime(timestamp,'%Y-%m-%d %H:%M:%S'),v_id=v_id))
            con.execute(query)
            return {'string_response': 'Volunteer Data Updated','status':True}
    except:
        return  {'string_response': 'Volunteer updation failed' ,'status':False}


# In[ ]:


def check_user(table_name,user_id):
    server_con = connections('db_read')
    query = """Select id from {table_name} where id={user_id}""".format(table_name=table_name,user_id=user_id)
    data = pd.read_sql(query,server_con)
    if (data.shape[0]>0):
        return {'string_response': 'User Existence validated','status':True}
    else:
        return {'string_response': 'ID does not exist in database','status':False}


# In[ ]:



