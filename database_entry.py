#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
from connections import connections,keys
import requests


# In[ ]:





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


def add_user(df):
    expected_columns=['creation_date', 'name', 'mob_number', 'email_id', 'password', 'access_type']
    if(df.columns==expected_columns):
        engine = connections('db_write')
        df.to_sql(name = 'users', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Data uploaded successfully'
        return True,return_str
    else:
        return_str = 'Column names not matching'
        return False,return_str
    
def check_user(username,password):
    server_con = connections('db_read')
    query = """Select mob_number,email_id,password,access_type from users"""
    volunteer_list = pd.read_sql(query,server_con)
    for i in volunteer_list.index:
        if(((volunteer_list.loc[i,'mob_number'].str==username) or (volunteer_list.loc[i,'email_id']==username)) and (volunteer_list.loc[i,'password'].str==password)):
            return_str = 'Login successful'
            return True,return_str
        elif(((volunteer_list.loc[i,'mob_number'].str==username) or (volunteer_list.loc[i,'email_id']==username)) and (volunteer_list.loc[i,'password'].str!=password)):
            return_str = 'Incorrect Password!'
        else:
            return_str = 'Incorrect username!'
        return False, return_str


#todo
#password encryption
#User info updation


# In[ ]:




