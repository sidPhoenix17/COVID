#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import datetime as dt
from settings import EARTH_RADIUS,moderator_list,server_type
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
    
        distance = EARTH_RADIUS * c
        if units=='m':
            return distance
        else:
            return distance / 1000.0
    except:
        raise
        return None


# In[ ]:


#Send message to all volunteers within 1km - to accept request
#Send message to all volunteers within 10kms - to help looking for volunteer
#Send message to all moderators about the both
def message_all_volunteers(lat,lon,radius,search_radius,uuid):
    v_list_q = """Select id as v_id,mob_number,name, latitude,longitude from volunteers where status=1"""
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_list['dist'] = get_haversine_distance(lat,lon,v_list['latitude'],v_list['longitude'])
    v_list = v_list.sort_values(by='dist',ascending=True)
    r_df = request_data_by_uuid(uuid)
    r_id = r_df.loc[0,'r_id']
    v_ids = pd.DataFrame()
    df = pd.DataFrame()
    df2 = pd.DataFrame()
    count=0
    for i in v_list.index:
        if(v_list.loc[i,'dist']<radius):
            link = "https://wa.me/918618948661?text=Hi%20I%20will%20help"
#             link = "covidsos.org/accept/"+uuid+"/"+v_list.loc[i,'mob_number']
            sms_text = '[COVIDSOS] Dear, '+v_list.loc[i,'name']+' someone in your area needs help. Request #'+(r_df.loc[0,'r_id'])+' Message us if you can volunteer '+link
            sms_to = int(v_list.loc[i,'mob_number'])
            df = df.append(v_list.loc[i,['v_id']])
            if(server_type=='prod'):
                send_sms(sms_text,sms_to,sms_type='transactional',send=True)
                print('SMS sent')
            else:
                print('Sending sms:',sms_text,' to ',str(sms_to))
        if((v_list.loc[i,'dist']>radius)&(v_list.loc[i,'dist']<search_radius)):
            count = count +1
            if(count>20):
                break
            link = "https://wa.me/918618948661?text=Refer"
            sms_text = '[COVIDSOS] Request #'+str(r_df.loc[0,'r_id'])+'. Volunteer needed in '+r_df.loc[0,'geoaddress'][0:40]+'. Please refer someone who can help '+link
            sms_to=int(v_list.loc[i,'mob_number'])
            df2 = df2.append(v_list.loc[i,['v_id']])
            if(server_type=='prod'):
                send_sms(sms_text,sms_to,sms_type='transactional',send=True)
                print('SMS sent')
            else:
                print('Sending sms:',sms_text,' to ',str(sms_to))
    df['r_id']=r_id
    df['status']='pending'
    print(v_list)
    print(df)
    print(df2)
    if(server_type=='prod'):
        engine = connections('prod_db_write')
        df.to_sql(name = 'nearby_volunteers', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
    mod_sms_text = "New request received. Sent to "+str(df.shape[0])+" nearby Volunteers and "+str(df2.shape[0])+" volunteers further away"
    mod_sms_text_2 = "New Request Name: "+r_df.loc[0,'name']+" Address: "+r_df.loc[0,'geoaddress'][0:50]+" Mob: "+str(r_df.loc[0,'mob_number'])+" Req:"+r_df.loc[0,'request']
    for i_number in moderator_list:
        if(server_type=='prod'):
            send_sms(mod_sms_text,sms_to=int(i_number),sms_type='transactional',send=True)
            send_sms(mod_sms_text_2,sms_to=int(i_number),sms_type='transactional',send=True)
            print('SMS sent')
            print('SMS sent')
        else:
            print('Sending sms:',mod_sms_text,' to ',str(i_number))
            print('Sending sms:',mod_sms_text_2,' to ',str(i_number))
    return None


# In[ ]:





# In[ ]:


def volunteer_accept(uuid,mob_number):
    v_list_q = """Select id as v_id,name as full_name from volunteers where mob_number='{mob_number}'""".format(mob_number=mob_number)
    v_list = pd.read_sql(v_list_q,connections('prod_db_read'))
    v_id = v_list.loc[0,'v_id']

    r_id_q = """Select id as r_id, mob_number as mob_number from requests where uuid='{uuid_str}'""".format(uuid_str=uuid)
    


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
    

