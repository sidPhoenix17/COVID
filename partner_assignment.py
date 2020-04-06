#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
import datetime as dt
from settings import EARTH_RADIUS,moderator_list
from connections import connections,write_query
from database_entry import send_sms
from data_fetching import request_data_by_uuid
import uuid


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


def message_all_volunteers(lat,lon,radius,uuid):
    v_list_q = """Select id as v_id,mob_number,name, latitude,longitude from volunteers where status=1"""
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_list['dist'] = get_haversine_distance(lat,lon,v_list['latitude'],v_list['longitude'])
    v_list = v_list.sort_values(by='dist',ascending=True)
    r_df = request_data_by_uuid(uuid)
    r_id = r_df.loc[0,'r_id']
    v_ids = pd.DataFrame()
    for i in v_list.index:
        if(v_list.loc[i,'dist']<radius):
            link = "covidsos.org/accept/"+uuid+"/"+v_list.loc[i,'mob_number']
            sms_text = '[COVIDSOS] Dear, '+v_list.loc[i,'name']+' someone in your area needs help. Click here to help '+link
            send_sms(sms_text,sms_to=int(v_list.loc[i,'mob_number']),sms_type='transactional',send=True)
            df = df.append(v_list.loc[i,['v_id']])
    if(v_list.shape[0]>0):
        mod_sms_text = "New request received. Forwarded to "+v_list.shape[0]+" Volunteers"
        for i_number in moderator_list:
            send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
        df['r_id']=r_id
        df['status']='pending'
        df.to_sql(name = 'nearby_volunteers', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
    else:
        mod_sms_text = " No nearby volunteers found for new request from "+r_df.oc[0,'geoaddress'],+"Mob: "+r_df.loc[0,'mob_number']
        for i_number in moderator_list:
            send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
    return None


# In[ ]:





# In[ ]:


def volunteer_accept(uuid,mob_number):
    v_list_q = """Select id as v_id,name as full_name from volunteers where mob_number='{mob_number}'""".format(mob_number=mob_number)
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_id = v_list.loc[0,'v_id']

    r_id_q = """Select id as r_id, mob_number as mob_number from requests where uuid='{uuid_str}'""".format(uuid_str=uuid)
    


# In[ ]:





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
    

