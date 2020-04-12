#!/usr/bin/env python
# coding: utf-8

# In[ ]:



import pandas as pd
from connections import connections,keys
import requests
import mailer_fn as mailer


# In[ ]:


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
        mailer.send_exception_mail()
        return {'Response':{},'status':False,'string_response':'Connection to DB failed'}


# In[ ]:


def get_private_map_data():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select timestamp,id as v_id, name,source,latitude,longitude,geoaddress,address,mob_number,email_id,status,source from volunteers"""
        v_df = pd.read_sql(v_q,server_con)
        v_df['timestamp']=pd.to_datetime(v_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)&(v_df['status']==1)]
        r_q = """Select timestamp,id as r_id, name,source,latitude,longitude,geoaddress,request,status,address,mob_number,source from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['timestamp']=pd.to_datetime(r_df['timestamp'])#.dt.tz_localize(tz='Asia/kolkata')
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        return {'Volunteers': v_df.to_dict('records'), 'Requests':r_df.to_dict('records')}
    except:
        mailer.send_exception_mail()
        return {}
    #return (v_df.to_json(orient='index'))
    
    


# In[ ]:


def get_public_map_data():
    try:
        server_con = connections('prod_db_read')
        v_q = """Select name,latitude,longitude,source from volunteers"""
        v_df = pd.read_sql(v_q,server_con)    
        v_df = v_df[(v_df['latitude']!=0.0)&(v_df['longitude']!=0.0)]
        v_df['name']='PRIVATE USER'
    #     v_df['radius']=0.5
    #     geometry = v_df.apply(lambda x: Point(x['longitude'],x['latitude']).buffer(buffer_radius*x.radius),axis=1)
    #     crs = {'init': 'epsg:4326'}
    #     v_df = gpd.GeoDataFrame(v_df, crs=crs, geometry=geometry)
        r_q = """Select name,request,latitude,longitude,source from requests"""
        r_df = pd.read_sql(r_q,server_con)
        r_df['name']='PRIVATE USER'
        r_df = r_df[(r_df['latitude']!=0.0)&(r_df['longitude']!=0.0)]
        return {'Volunteers': v_df.to_dict('records'), 'Requests':r_df.to_dict('records')}
    except:
        mailer.send_exception_mail()
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
        mailer.send_exception_mail()
        return {'pending':{},'completed':{}}


# In[ ]:


def website_success_stories():
    try:
        server_con = connections('prod_db_read')
        query = """Select * from success_stories"""
        query_df = pd.read_sql(query,server_con)
        return {'instagram':query_df.to_dict('records')}
    except:
        mailer.send_exception_mail()
        return {'instagram':{}}


# In[ ]:



def get_user_id(username, password):
    server_con = connections('prod_db_read')
    query = f"""Select id, access_type from users where mob_number='{username}' or email_id='{username}' and password='{password}' order by id desc limit 1"""
    try:
        data = pd.read_sql(query, server_con)
        user_id = int(data.loc[0,'id'])
        access_type = int(data.loc[0,'access_type'])
        return user_id, access_type
    except:
        mailer.send_exception_mail()
        return None, None
    


# In[ ]:


def verify_user_exists(user_id, access_type):
    server_con = connections('prod_db_read')
    query = f"""Select id from users where id='{user_id}' and access_type='{access_type}' order by id desc limit 1"""
    try:
        data = pd.read_sql(query, server_con)
        return (True if data.shape[0] > 0 else False)
    except:
        mailer.send_exception_mail()
        return False

def verify_volunteer_exists(mob_number, v_id=None, country=None):
    server_con = connections('prod_db_read')
    query = f"""Select id, country from volunteers where mob_number='{mob_number}'"""
    if v_id and country:
        query = f"""Select id, country from volunteers where id='{v_id}' and country='{country}'"""
    try:
        data = pd.read_sql(query, server_con)
        if data.shape[0] > 0:
            return {'status': True, 'volunteer_id': data.loc[0, 'id'], 'country': data.loc[0, 'country']}
        return {'status': False, 'volunteer_id': None, 'country': None}
    except:
        mailer.send_exception_mail()
        return {'status': False, 'volunteer_id': None, 'country': None}


# In[ ]:


def accept_request_page(uuid):
    query = """Select r.id as r_id,r.status as status, r.geoaddress as request_address,r.latitude as latitude, r.longitude as longitude,
            rv.what as what, rv.why as why, rv.verification_status as verification_status
            from requests r left join request_verification rv on r.id=rv.r_id
            where r.uuid='{uuid}'""".format(uuid=uuid)
    df = pd.read_sql(query,connections('prod_db_read'))
    return df
    
    
def request_data_by_uuid(uuid):
    r_id_q = """Select id as r_id,name,mob_number,geoaddress,latitude,longitude,request,status,timestamp from requests where uuid='{uuid_str}'""".format(uuid_str=uuid)
    try:
        r_id_df = pd.read_sql(r_id_q,connections('prod_db_read'))
        return r_id_df
    except:
        mailer.send_exception_mail()
        return pd.DataFrame()
    

def request_data_by_id(r_id):
    r_id_q = """Select id as r_id,name,mob_number,geoaddress,latitude,longitude,request,status,timestamp from requests where id='{r_id}'""".format(r_id=r_id)
    try:
        r_id_df = pd.read_sql(r_id_q,connections('prod_db_read'))
        return r_id_df
    except:
        mailer.send_exception_mail()
        return pd.DataFrame()
    

def volunteer_data_by_id(v_id):
    v_id_q = """Select id as v_id,name,mob_number from volunteers where id='{v_id}'""".format(v_id=v_id)
    try:
        v_id_df = pd.read_sql(v_id_q,connections('prod_db_read'))
        return v_id_df
    except:
        mailer.send_exception_mail()
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

