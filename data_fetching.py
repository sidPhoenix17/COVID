#!/usr/bin/env python
# coding: utf-8

# In[ ]:



import pandas as pd
from connections import connections,keys
import requests


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
        pending_request_count = r_df[r_df['status']=='pending'].shape[0]
        return {'Response':{'volunteer_count':volunteer_count,'request_count':request_count,'pending_request_count':pending_request_count},'status':True,'string_response':'Metrics computed'}
    except:
        return {'Response':{},'status':False,'string_response':'Connection to DB failed'}


# In[ ]:


def get_private_map_data():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select timestamp,id as v_id, name,source,latitude,longitude,address,mob_number,email_id,status from volunteers"""
        v_df = pd.read_sql(v_q,server_con)
        v_df['timestamp']=pd.to_datetime(v_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)&(v_df['status']==1)]
        v_df['type']='Volunteer'
        r_q = """Select timestamp,id as r_id, name,age,source,latitude,longitude,request,status,address,mob_number from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['timestamp']=pd.to_datetime(r_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        r_df['type']='Request'
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
        v_df['type']='Volunteer'
    #     v_df['radius']=0.5
    #     geometry = v_df.apply(lambda x: Point(x['longitude'],x['latitude']).buffer(buffer_radius*x.radius),axis=1)
    #     crs = {'init': 'epsg:4326'}
    #     v_df = gpd.GeoDataFrame(v_df, crs=crs, geometry=geometry)
        r_q = """Select name,age,request,latitude,longitude from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['name']='PRIVATE USER'
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        r_df['type']='Request'
        return {'Volunteers': v_df.to_dict('records'), 'Requests':r_df.to_dict('records')}
    except:
        return {}


# In[ ]:





# In[ ]:





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

