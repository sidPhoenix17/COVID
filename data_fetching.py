#!/usr/bin/env python
# coding: utf-8

# In[2]:



import pandas as pd
from connections import connections,keys
import requests


# In[3]:


def get_requests_list():
    req_q = """Select * from request_status"""
    req_df = pd.read_sql(req_q, connections('prod_db_read'))
    return req_df.to_dict('records')


# In[ ]:


def get_ticker_counts():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select * from volunteers"""
        v_df = pd.read_sql(v_q,server_con)
        r_q = """Select * from requests"""
        r_df = pd.read_sql(r_q,server_con)

        volunteer_count = v_df['mob_number'].nunique()
        request_count = r_df.shape[0]
        pending_request_count = r_df[r_df['status'].isin(['received','verified','pending'])].shape[0]
        return {'Response':{'volunteer_count':volunteer_count,'request_count':request_count,'pending_request_count':pending_request_count},'status':True,'string_response':'Metrics computed'}
    except:
        return {'Response':{},'status':False,'string_response':'Connection to DB failed'}


# In[ ]:


def get_private_map_data():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select timestamp,id as v_id, name,source,latitude,longitude,geoaddress,address,mob_number,email_id,status from volunteers"""
        v_df = pd.read_sql(v_q,server_con)
        v_df['timestamp']=pd.to_datetime(v_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)&(v_df['status']==1)]
        r_q = """Select timestamp,id as r_id, name,source,latitude,longitude,geoaddress,request,status,address,mob_number from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['timestamp']=pd.to_datetime(r_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        return {'Volunteers': v_df.to_dict('records'), 'Requests':r_df.to_dict('records')}
    except:
        return {}
    #return (v_df.to_json(orient='index'))
    
    


# In[ ]:


def get_public_map_data():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select name,latitude,longitude from volunteers"""
        v_df = pd.read_sql(v_q,server_con)    
        v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)]
        v_df['name']='PRIVATE USER'
    #     v_df['radius']=0.5
    #     geometry = v_df.apply(lambda x: Point(x['longitude'],x['latitude']).buffer(buffer_radius*x.radius),axis=1)
    #     crs = {'init': 'epsg:4326'}
    #     v_df = gpd.GeoDataFrame(v_df, crs=crs, geometry=geometry)
        r_q = """Select name,request,latitude,longitude from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['name']='PRIVATE USER'
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        return {'Volunteers': v_df.to_dict('records'), 'Requests':r_df.to_dict('records')}
    except:
        return {}


# In[ ]:


def website_requests_display():
    try:
        server_con = connections('prod_db_read')
        query = """Select * from website_display"""
        query_df = pd.read_sql(query,server_con)
        pending_queries = query_df[query_df['type'].isin(['received','verified','pending'])]
        completed_queries = query_df[query_df['type']=='completed']
        return {'pending':pending_queries.to_dict('records'),'completed':completed_queries.to_dict('records')}
    except:
        return {'pending':{},'completed':{}}


# In[ ]:



def get_user_id(username, password):
    server_con = connections('prod_db_read')
    query = f"""Select id from users where mob_number='{username}' or email_id='{username}' and password='{password}' order by id desc limit 1"""
    try:
        data = pd.read_sql(query, server_con)
        user_id = int(data.iloc[0]['id'])
        return user_id
    except:
        return None
    


# In[ ]:


def accept_request_page(uuid,v_mob_number):
    query = """Select rm.r_id, rm.v_id,v.name as volunteer_name,rm.status, r.geoaddress as request_address,r.latitude as latitude, r.longitude as longitude, r.request as request_details
            from nearby_volunteers rm left join requests r on r.id=rm.r_id
            left join volunteers v on v.id=rm.v_id
            where v.mob_number={mob_number} and r.uuid='{uuid}'""".format(uuid=uuid,mob_number=v_mob_number)
    df = pd.read_sql(query,connections('prod_db_read'))
    return df
    
    
def request_data_by_uuid(uuid):
    r_id_q = """Select id as r_id,name,mob_number,geoaddress,latitude,longitude,request,status from requests where uuid='{uuid_str}'""".format(uuid_str=uuid)
    try:
        r_id_df = pd.read_sql(r_id_q,connections('prod_db_read'))
        return r_id_df
    except:
        return pd.DataFrame()
    

def request_data_by_id(r_id):
    r_id_q = """Select id as r_id,name,mob_number,geoaddress,latitude,longitude,request,status from requests where id='{r_id}'""".format(r_id=r_id)
    try:
        r_id_df = pd.read_sql(r_id_q,connections('prod_db_read'))
        return r_id_df
    except:
        return pd.DataFrame()
    

def volunteer_data_by_id(v_id):
    v_id_q = """Select id as v_id,name,mob_number from volunteers where id='{v_id}'""".format(v_id=v_id)
    try:
        v_id_df = pd.read_sql(v_id_q,connections('prod_db_read'))
        return v_id_df
    except:
        return pd.DataFrame()


# In[ ]:


# def folium_data_request():
#     server_con = connections('prod_db_read')
#     v_q = """Select id as v_id, name,source,latitude,longitude from volunteers"""
#     v_df = pd.read_sql(v_q,server_con)    
#     v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)]
#     v_df['type']='Volunteer'
# #     v_df['radius']=0.5
# #     geometry = v_df.apply(lambda x: Point(x['longitude'],x['latitude']).buffer(buffer_radius*x.radius),axis=1)
# #     crs = {'init': 'epsg:4326'}
# #     v_df = gpd.GeoDataFrame(v_df, crs=crs, geometry=geometry)
#     r_q = """Select id as r_id, name,source,latitude,longitude,request,status from requests"""
#     r_df = pd.read_sql(r_q,server_con)
#     r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
#     r_df['type']='Request'
#     return v_df,r_df

