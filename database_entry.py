#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from connections import connections,keys
import requests


# In[2]:





# In[ ]:



def remove_duplicates(df,user_type):
    server_con = connections('db_read')
    if(user_type=='volunteers')
        query = """Select mob_number from volunteers"""
        volunteer_list = pd.read_sql(query,server_con)
        df_new = df[!(df['mob_number'].isin(volunteer_list['mob_number'].unique()))]
    elif(user_type=='requests')
        query = """Select timestamp, mob_number from requests"""
        request_list = pd.read_sql(query,server_con)
        df_new = df.merge(request_list[['timestamp','mob_number','name']], how='left',on=['timestamp','mob_number'],suffixes=('','_r'))
        df_new = df_new[df_new['name_r'].isnull()]
    return df_new
    
def add_volunteers(df):
    #df with columns [timestamp, name, mob_number, email_id, country, address, geoaddress,latitude, longitude, source]
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source']
    if(df.columns==expected_columns):
        engine = connections('db_write')
        df.to_sql(name = 'volunteers', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Data uploaded successfully'
        return True,return_str
    else:
        return_str = 'Column names not matching'
        return False,return_str

def add_requests(df):
    #df with columns [timestamp, name,mob_number, email_id, country, address, geoaddress, latitude, longitude, source, request,age]
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']
    if(df.columns==expected_columns):
        engine = connections('db_write')
        df.to_sql(name = 'requests', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)
        return_str = 'Data uploaded successfully'
        return True,return_str
    else:
        return_str = 'Column names not matching'
        return False,return_str


# In[6]:


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




