#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
import datetime as dt
from settings import EARTH_RADIUS
from connections import connections,write_query
from database_entry import send_sms
import uuid


# In[ ]:





# In[ ]:



def get_haversine_distance(start_lat, start_lng, end_lat, end_lng, units='km'):
    try:
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(np.radians, [start_lng, start_lat, end_lng, end_lat])
    
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (np.sin(dlat / 2) ** 2 + np.cos(lat1) *
             np.cos(lat2) * np.sin(dlon / 2) ** 2)
        c = 2 * np.arcsin(np.sqrt(a))
    
        distance = settings.EARTH_RADIUS * c
        if units=='m':
            return distance
        else:
            return distance / 1000.0
    except:
        return None


# In[ ]:


def auto_assign_volunteer(lat,lon,link):
    v_list_q = """Select id as v_id,mob_number,name, latitude,longitude from volunteers where status=1"""
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_list['dist'] = get_haversine_distance(lat,lon,)
    v_list = v_list.sort_values(by='dist',ascending=True)
    for i in v_list.index:
        if(v_list.loc[i,'dist']<'radius'):
            sms_text = 'Dear, '+v_list.loc[i,'name']+' someone in your area needs help. Click here to help '+link
            send_sms(sms_text,sms_to=v_list.loc[i,'mob_number'],sms_type='transactional',send=True)
    #incomplete
    return None
    


# In[ ]:


def generate_uuid():
    uuid_key = str(uuid.uuid4()).replace('-', '')
    return uuid_key


# In[ ]:


def assignment_link(r_id):
    v_list_q = """Select id as v_id,mob_number,name, latitude,longitude from volunteers where status=1"""
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_list['dist'] = get_haversine_distance(lat,lon,)
    v_list = v_list.sort_values(by='dist',ascending=True)
    for i in v_list.index:
        if(v_list.loc[i,'dist']<'radius'):
            sms_text = 'Dear, '+v_list.loc[i,'name']+' someone in your area needs help. Click here to help '+link
            send_sms(sms_text,sms_to=v_list.loc[i,'mob_number'],sms_type='transactional',send=True)
    #incomplete
    return None
    

