#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests, json
import pandas as pd
import datetime as dt
from connections import connections,keys,write_query
import requests
from sqlalchemy.sql import text
import datetime as dt
from settings import sms_key, sms_sid, sms_url, otp_url, EARTH_RADIUS,server_type,org_request_list
import mailer_fn as mailer
import json
import requests


# In[ ]:



#todo - AddUser
#Check if User Exists
#password encryption


# In[ ]:


def remove_existing_volunteers(df):
    try:
        server_con = connections('prod_db_read')
        query = """Select mob_number from volunteers"""
        volunteer_list = pd.read_sql(query,server_con)
        df['mob_number']=df['mob_number'].str.replace(" ",'')
        df['mob_number']=df['mob_number'].str.replace(",",'')
        df['mob_number']=df['mob_number'].str.replace("\+91",'')
        df['mob_number']=df['mob_number'].apply(lambda x: int(x))
        df_new = df[df['mob_number'].isin(volunteer_list['mob_number'].unique())==False]
        return df_new
    except:
        mailer.send_exception_mail()
        return df
    
def last_entry_timestamp(source):
    server_con = connections('prod_db_read')
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
    expected_columns=['timestamp', 'name','mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude','source','status','support_type']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'volunteers', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return_str = 'Volunteer Data Submitted'
        return True,return_str
    else:
        return_str = 'Data format not matching'
        return False,return_str

def add_requests(df):
    #df with columns [timestamp, name,mob_number, email_id, country, address, geoaddress, latitude, longitude, source, request,age]
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age','status','uuid']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'requests', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return_str = 'Request submitted successfully'
        return True,return_str
    else:
        return_str = 'Data Format not matching'
        return False,return_str

def contact_us_form_add(df):
    mimetype_parts_dict={'html':df.to_html()}
    mailer.send_email(org_request_list, [], [],'[COVIDSOS] New Request from an organisation', mimetype_parts_dict)
    expected_columns=['timestamp', 'name','organisation', 'mob_number', 'email_id', 'comments','source']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'org_requests', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return_str = 'Request submitted successfully'
        return True,return_str
    else:
        return_str = 'Data Format not matching'
        return False,return_str


# In[ ]:


def add_request_verification_db(df):
    expected_columns=['timestamp', 'r_id','what', 'why', 'where', 'verification_status','verified_by','financial_assistance']
    #If Request ID does not exist in verification table, create a new row
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'request_verification', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return_str = 'Request verification data submitted successfully'
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
        mailer.send_exception_mail()
        return None


# In[ ]:



def verify_user(username,password):
    server_con = connections('prod_db_read')
    query = """Select users.id as id,name as full_name, mob_number,email_id,password,user_access.type as type from users left join user_access on users.access_type=user_access.id"""
    user_list = pd.read_sql(query,server_con)
    for i in user_list.index:
        if(((str(user_list.loc[i,'mob_number'])==username) or (user_list.loc[i,'email_id']==username)) and (user_list.loc[i,'password']==password)):
            output = {'Response':{'access_level': user_list.loc[i,'type'],'username':username,'user_id':str(user_list.loc[i,'id']),'full_name':user_list.loc[i,'full_name']},'string_response': 'Login successful','status':True}
            break
        elif(((str(user_list.loc[i,'mob_number'])==username) or (user_list.loc[i,'email_id']==username)) and (user_list.loc[i,'password']!=password)):
            output = {'Response':{'username':username},'string_response': 'Incorrect Password','status':False}
            break
        else:
            output = {'Response':{'username':username},'string_response': 'Incorrect Username','status':False}
    return output


# In[ ]:



def add_user(df):
    expected_columns=['creation_date', 'name', 'mob_number', 'email_id', 'organisation', 'password', 'access_type','created_by']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'users', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return  {'Response':{},'string_response': 'User Added Successfully','status':True}
    else:
        return  {'Response':{},'string_response': 'User addition failed due to incorrect data format' ,'status':False}
    


# In[ ]:



def request_matching(df):
    expected_columns=['request_id','volunteer_id','matching_by','timestamp']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'request_matching', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return  {'Response':{},'string_response': 'Volunteer Assigned','status':True}
    else:
        return  {'Response':{},'string_response': 'Volunteer assignment failed due to incorrect data format' ,'status':False}
        


# In[ ]:



def check_user(table_name,user_id):
    server_con = connections('prod_db_read')
    errorResponse = {'Response':{},'string_response': 'Requesting user ID does not exist in database','status':False}
    try:
        query = """Select id from {table_name} where id={user_id}""".format(table_name=table_name,user_id=user_id)
        data = pd.read_sql(query,server_con)
        if (data.shape[0]>0):
            return {'Response':{},'string_response': 'User Existence validated','status':True}
        else:
            return errorResponse
    except:
        mailer.send_exception_mail()
        return errorResponse


# In[ ]:



def update_requests_db(r_dict_where,r_dict_set):
    try:
        set_sql_format = ",".join(("{column_name}='{value}'".format(column_name = x,value = r_dict_set[x]) for x in r_dict_set))
        where_sql_format = " and ".join(("{column_name}='{value}'".format(column_name = x,value = r_dict_where[x]) for x in r_dict_where))
        query = """update requests set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request info updation failed' ,'status':False}

def update_nearby_volunteers_db(nv_dict_where,nv_dict_set):
    try:
        set_sql_format = ",".join(("{column_name}='{value}'".format(column_name = x,value = nv_dict_set[x]) for x in nv_dict_set))
        where_sql_format = " and ".join(("{column_name}='{value}'".format(column_name = x,value = nv_dict_where[x]) for x in nv_dict_where))
        query = """update nearby_volunteers set {set_str} where {where_str};""".format(set_str= set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'nearby_volunteers info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'nearby_volunteers info updation failed' ,'status':False}

def update_volunteers_db(v_dict_where,v_dict_set):
    try:
        set_sql_format = ",".join(("{column_name}='{value}'".format(column_name = x,value = v_dict_set[x]) for x in v_dict_set))
        where_sql_format = " and ".join(("{column_name}='{value}'".format(column_name = x,value = v_dict_where[x]) for x in v_dict_where))
        query = """update volunteers set {set_str} where {where_str};""".format(set_str= set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Volunteer info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Volunteer info updation failed' ,'status':False}

    
def update_request_v_db(rv_dict_where,rv_dict_set):
    try:
        set_sql_format = ",".join(("{column_name}='{value}'".format(column_name = x,value = rv_dict_set[x]) for x in rv_dict_set))
        where_sql_format = " and ".join(("{column_name}='{value}'".format(column_name = x,value = rv_dict_where[x]) for x in rv_dict_where))
        query = """update request_verification set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request Verification info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request Verification info updation failed' ,'status':False}


# In[ ]:





# In[ ]:



def blacklist_token(token): 
    query = f"""insert into token_blacklist (token) values ('{token}');"""
    try:
        write_query(query,'prod_db_write')
        return True
    except:
        mailer.send_exception_mail()
        return False


# In[ ]:



def send_sms(sms_text,sms_to=9582148040,sms_type='transactional',send=True):
    sid = sms_sid
    key = sms_key
    url = sms_url
    if(sms_type=='transactional'):
        route="4"
    elif(sms_type=='promotional'):
        route="1"
    data = {"sender": "SOCKET","route": route,"country": "91","sms": [{"message": sms_text,"to": [sms_to]}]}
    headers = {'Content-type': 'application/json', 'authkey': key}
    if ((send)&(server_type!='local')):
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers)
            sms_dict = {'sms_text':[sms_text],'sms_type':[sms_type],'sms_to':[sms_to],'sms_status_type':[r.status_code],'sms_json_response':[str(r.json())]}
            new_sms_df = pd.DataFrame(sms_dict)
            engine = connections('prod_db_write')
            new_sms_df.to_sql(name = 'sms_log', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
            return None
        except:
            print('SMS API error')
            mailer.send_exception_mail()
            return None


# In[ ]:



def send_otp(otp_to):
    # if server_type=='local':
    #     return 'server_type is local', False
    try:
        r = requests.post(otp_url, params={"authkey": sms_key, "mobile": f'91{otp_to}'})
        r = r.json()
    except:
        mailer.send_exception_mail()
        return 'otp api failure', False
    if r['type'] == 'success':
        return r['request_id'], True
    return r['message'], False


# In[ ]:



def resend_otp(otp_to):
    url = otp_url + '/retry'
    # if server_type=='local':
    #     return 'server_type is local', False
    try:
        r = requests.post(url, params={"authkey": sms_key, "mobile": f'91{otp_to}'})
        r = r.json()
    except:
        mailer.send_exception_mail()
        return 'resend otp api failure', False
    return r['message'], r['type'] == 'success'


# In[ ]:



def verify_otp(otp, otp_from):
    url = otp_url + '/verify'
    # if server_type=='local':
    #     return 'server_type is local', False
    try:
        r = requests.post(url, params={"authkey": sms_key, "mobile": f'91{otp_from}', "otp": otp})
        r = r.json()
    except:
        mailer.send_exception_mail()
        return 'verify otp api failure', False
    return r['message'], r['type'] == 'success'


# In[ ]:





# In[ ]:


# def volunteer_updation(v_id,column,new_value,timestamp):
#     engine = connections('prod_db_write')
#     try:
#         with engine.connect() as con:
#             query = text("""update volunteers set {column_name}='{new_value}',last_updated='{timestamp}' 
#             where id={v_id};""".format(column_name=column,new_value=new_value, timestamp =dt.datetime.strftime(timestamp,'%Y-%m-%d %H:%M:%S'),v_id=v_id))
#             con.execute(query)
#             return {'Response':{},'string_response': 'Volunteer Data Updated','status':True}
#     except:
#         return  {'Response':{},'string_response': 'Volunteer updation failed' ,'status':False}

# def request_updation(r_id,column,new_value,timestamp):
#     engine = connections('prod_db_write')
#     try:
#         with engine.connect() as con:
#             query = text("""update requests set {column_name}='{new_value}',last_updated='{timestamp}' 
#             where id={r_id};""".format(column_name=column,new_value=new_value, timestamp =dt.datetime.strftime(timestamp,'%Y-%m-%d %H:%M:%S'),r_id=r_id))
#             con.execute(query)
#             return {'Response':{},'string_response': 'Request Updated','status':True}
#     except e:
#         return  {'Response':{},'string_response': 'Volunteer updation failed' ,'status':False}


# In[ ]:





# In[ ]:





# In[ ]:




