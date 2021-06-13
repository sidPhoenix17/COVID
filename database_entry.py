#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests, json
import pandas as pd
from lib.redis import redis
from connections import connections,write_query
from settings import sms_key, sms_sid, sms_url,sms_url_v2, otp_url,server_type,org_request_list, raven_key, raven_sms_url
import mailer_fn as mailer
from message_templates import otp_template_id

# In[ ]:

def check_volunteer_exists(df):
    try:
        server_con = connections('prod_db_read')
        query = """Select id from volunteers where `mob_number`='{mob_number}'""".format(mob_number=df.loc[0,'mob_number'])
        volunteer_list = pd.read_sql(query,server_con)
        if(volunteer_list.shape[0]>0):
            return True,volunteer_list.loc[0,'id']
        else:
            return False,None
    except:
        mailer.send_exception_mail()
        return False,None

def last_entry_timestamp(source):
    server_con = connections('prod_db_read')
    query = """Select max(timestamp) as timestamp from requests where source='{source}'""".format(source=source)
    max_timestamp = pd.read_sql(query,server_con,parse_dates=['timestamp'])
    max_timestamp['source']=source
    return max_timestamp


# In[ ]:



def add_volunteers_to_db(df):
    expected_columns = ['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude','longitude', 'source', 'status', 'support_type','city']
    try:
        df.loc[0, 'address'] = sanitise_for_sql({'message': df.loc[0, 'address']}).get('message', '')
        df.loc[0, 'geoaddress'] = sanitise_for_sql({'message': df.loc[0, 'geoaddress']}).get('message', '')
        if (len(df.columns.intersection(expected_columns)) == len(expected_columns)):
            exists,v_id = check_volunteer_exists(df)
            df['timestamp']=pd.to_datetime(df['timestamp'])
            if(exists):
                req_dict = df.loc[0,expected_columns].to_dict()
                update_volunteers_db({'id':v_id},req_dict)
                return_str = 'Volunteer already exists. Your information has been updated'
                return True, return_str
            else:
                engine = connections('prod_db_write')
                df.to_sql(name='volunteers', con=engine, schema='covidsos', if_exists='append', index=False,
                          index_label=None)
                return_str = 'Volunteer Data Submitted'
                return True, return_str
        else:
            print(df.loc[0].to_dict(),flush=True)
            return_str = 'Data format not matching'
            return False,return_str
    except Exception as e:
        print(df.loc[0].to_dict(),flush=True)
        print(e,flush=True)
        return_str = 'Error'
        mailer.send_exception_mail()
        return False,return_str

def add_requests(df):
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source','members_impacted', 'request', 'age','status','uuid', 'managed_by','city','volunteers_reqd','filled_by_name','filled_by_mob_number']
    try:
        if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
            engine = connections('prod_db_write')
            df.to_sql(name = 'requests', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
            return_str = 'Request submitted successfully'
            return True,return_str
        else:
            print(df.loc[0].to_dict(),flush=True)
            return_str = 'Data Format not matching'
            return False,return_str
    except Exception as e:
        print(df.loc[0].to_dict(),flush=True)
        print(e,flush=True)
        return_str = 'Error'
        mailer.send_exception_mail()
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
    expected_columns=['timestamp', 'r_id','what', 'why', 'where', 'verification_status','verified_by','financial_assistance', 'urgent']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        df.loc[0, 'what'] = sanitise_for_sql({'message': df.loc[0, 'what']}).get('message', '')
        df.loc[0, 'why'] = sanitise_for_sql({'message': df.loc[0, 'why']}).get('message', '')
        df.loc[0, 'where'] = sanitise_for_sql({'message': df.loc[0, 'where']}).get('message', '')
        engine = connections('prod_db_write')
        df.to_sql(name = 'request_verification', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return_str = 'Request verification data added successfully'
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

#TODO - extract city from location
def get_city(lat, lon):
# - check if places ID is sent via Google address API
# - check if places ID is sent via Google address API
# Else extract using reverse Geocoding API
#     geolocator = GoogleV3(api_key='')
#     locations = geolocator.reverse("{},{} ".format(lat, lon), exactly_one=False)
#     location = None
#     if locations is not None and isinstance(locations, list):
#         for loc in locations:
#             if len(loc.address.split(",")) == 3:
#                 location = loc.address
#                 break
#         if location is None:
#             try:
#                 location = locations[0]
#             except IndexError:
#                 location = None
#     return location if location is not None else location
    return None
# In[ ]:




# TODO: sanitise df data for single quotes
def add_user(df):
    expected_columns=['creation_date', 'name', 'mob_number', 'email_id', 'organisation', 'password', 'access_type','created_by','verification_team']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'users', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return  {'Response':{},'string_response': 'User Added Successfully','status':True}
    else:
        return  {'Response':{},'string_response': 'User addition failed due to incorrect data format' ,'status':False}


def add_message(message_id, from_number, to_number, message, message_format, channel, message_type):
    message_dict = {'message_id': [message_id], 'from': [from_number], 'to': [to_number],
                         'message': [message], 'type': [message_format], 'channel': [channel],
                         'message_type': [message_type]}
    new_message_df = pd.DataFrame(message_dict)
    try:
        engine = connections('prod_db_write')
        new_message_df.to_sql(name='messages', con=engine, schema='covidsos', if_exists='append', index=False, index_label=None)
        return {'Response':{},'string_response': 'Message Added Successfully','status':True}
    except:
        return {'Response':{},'string_response': 'Message addition failed due to incorrect data format' ,'status':False}


def add_cron_job(df):
    expected_columns = ['created_by', 'is_deleted', 'updated_by', 'cron_expression', 'task_ref']
    if (len(df.columns.intersection(expected_columns)) == len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name='schedule', con=engine, schema='covidsos', if_exists='append', index=False, index_label=None)
        return {'Response': {}, 'string_response': 'Cron Added Successfully', 'status': True}
    else:
        return {'Response': {}, 'string_response': 'Cron addition failed due to incorrect data format', 'status': False}


# In[ ]:


# TODO: sanitise df data for single quotes
def request_matching(df):
    expected_columns=['request_id','volunteer_id','matching_by','timestamp']
    if(len(df.columns.intersection(expected_columns))==len(expected_columns)):
        engine = connections('prod_db_write')
        df.to_sql(name = 'request_matching', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
        return  {'Response':{},'string_response': 'Volunteer Assigned','status':True}
    else:
        return  {'Response':{},'string_response': 'Volunteer assignment failed due to incorrect data format' ,'status':False}



# In[ ]:


def sanitise_for_sql(obj):
    if not isinstance(obj, dict):
        return {}
    for i,j in obj.items():
        if isinstance(j, str) and "'" in j:
            obj[i] = j.replace("'", "''")
    return obj


# In[ ]:

def update_requests_db(r_dict_where,r_dict_set):
    try:
        r_dict_where, r_dict_set = sanitise_for_sql(r_dict_where), sanitise_for_sql(r_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = r_dict_set[x]) for x in r_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = r_dict_where[x]) for x in r_dict_where))
        query = """update requests set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request info updation failed' ,'status':False}

def update_nearby_volunteers_db(nv_dict_where,nv_dict_set):
    try:
        nv_dict_where,nv_dict_set = sanitise_for_sql(nv_dict_where), sanitise_for_sql(nv_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = nv_dict_set[x]) for x in nv_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = nv_dict_where[x]) for x in nv_dict_where))
        query = """update nearby_volunteers set {set_str} where {where_str};""".format(set_str= set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'nearby_volunteers info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'nearby_volunteers info updation failed' ,'status':False}

def update_volunteers_db(v_dict_where,v_dict_set):
    try:
        v_dict_where,v_dict_set = sanitise_for_sql(v_dict_where), sanitise_for_sql(v_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = v_dict_set[x]) for x in v_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = v_dict_where[x]) for x in v_dict_where))
        query = """update volunteers set {set_str} where {where_str};""".format(set_str= set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Volunteer info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Volunteer info updation failed' ,'status':False}

def update_users_db(r_dict_where,r_dict_set):
    try:
        r_dict_where, r_dict_set = sanitise_for_sql(r_dict_where), sanitise_for_sql(r_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = r_dict_set[x]) for x in r_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = r_dict_where[x]) for x in r_dict_where))
        query = """update users set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'User info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'User info updation failed' ,'status':False}


def update_request_v_db(rv_dict_where,rv_dict_set):
    try:
        rv_dict_where,rv_dict_set = sanitise_for_sql(rv_dict_where), sanitise_for_sql(rv_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = rv_dict_set[x]) for x in rv_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = rv_dict_where[x]) for x in rv_dict_where))
        query = """update request_verification set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request Verification info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request Verification info updation failed' ,'status':False}


def update_request_updates_db(ru_dict_where,ru_dict_set):
    try:
        ru_dict_where,ru_dict_set = sanitise_for_sql(ru_dict_where), sanitise_for_sql(ru_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = ru_dict_set[x]) for x in ru_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = ru_dict_where[x]) for x in ru_dict_where))
        query = """update request_updates set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request Update info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request Update info updation failed' ,'status':False}


def update_schedule_db(ru_dict_where,ru_dict_set):
    try:
        ru_dict_where,ru_dict_set = sanitise_for_sql(ru_dict_where), sanitise_for_sql(ru_dict_set)
        set_sql_format = ",".join(("`{column_name}`='{value}'".format(column_name = x,value = ru_dict_set[x]) for x in ru_dict_set))
        where_sql_format = " and ".join(("`{column_name}`='{value}'".format(column_name = x,value = ru_dict_where[x]) for x in ru_dict_where))
        query = """update schedule set {set_str} where {where_str};""".format(set_str = set_sql_format,where_str=where_sql_format)
        write_query(query,'prod_db_write')
        return {'Response':{},'string_response': 'Request Update info Updated','status':True}
    except:
        mailer.send_exception_mail()
        return  {'Response':{},'string_response': 'Request Update info updation failed' ,'status':False}


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
    try:
        redis_key = "sms_channel"
        info = {
            "text": sms_text,
            "phone_number": sms_to,
            "type": sms_type
        }
        jsonInfo = json.dumps(info)
        redis.lpush(redis_key, jsonInfo)
    except Exception as e:
        print("Problem in storing sms, sending directly", str(e),flush=True)
        return send_sms_to_phone(sms_text, sms_to, sms_type, send)

def send_sms_to_phone(sms_text,sms_to=9582148040,sms_type='transactional',send=True):
    if((send)&(server_type!='local')):
        send_raven_v1("a_new_temp",sms_to,True,{"var1":sms_text[0:28],"var2":sms_text[29:57],"var3":sms_text[58:86],"var4":sms_text[87:115]})
    return None
    # sid = sms_sid
    # key = sms_key
    # url = sms_url
    # if(sms_type=='transactional'):
    #     route="4"
    # elif(sms_type=='promotional'):
    #     route="1"
    # data = {"sender": "SOCKET","route": route,"country": "91","sms": [{"message": sms_text,"to": [sms_to]}]}
    # headers = {'Content-type': 'application/json', 'authkey': key}
    # if ((send)&(server_type!='local')):
    #     try:
    #         r = requests.post(url, data=json.dumps(data), headers=headers)
    #         if(r.status_code==200):
    #             sms_dict = {'sms_text':[sms_text],'sms_type':[sms_type],'sms_to':[sms_to],'sms_status_type':[r.status_code],'sms_json_response':[str(r.json())]}
    #         else:
    #             sms_dict = {'sms_text': [sms_text], 'sms_type': [sms_type], 'sms_to': [sms_to],'sms_status_type': [r.status_code], 'sms_json_response': ['{}']}
    #         new_sms_df = pd.DataFrame(sms_dict)
    #         engine = connections('prod_db_write')
    #         new_sms_df.loc[0, 'sms_text'] = sanitise_for_sql({'message': new_sms_df.loc[0, 'sms_text']}).get('message', '')
    #         new_sms_df.to_sql(name = 'sms_log', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
    #         return None
    #     except:
    #         print('SMS API error',flush=True)
    #         mailer.send_exception_mail()
    #         return None
#
# def send_sms_to_phone_v2(msg_template_id,sms_to=919582148040,send=True,body_parameters={}):
#     key = sms_key
#     url = sms_url_v2
#     data = {"mobiles" : sms_to,"flow_id" : msg_template_id}
#     data.update(body_parameters)
#     headers = {'Content-type': 'application/json', 'authkey': key}
#     if ((send)&(server_type!='local')):
#         try:
#             r = requests.post(url, data=json.dumps(data), headers=headers)
#             if(r.status_code==200):
#                 sms_text = sms_converter(template_id,body_parameters)
#                 sms_dict = {'sms_text':[sms_text],'sms_type':[sms_type],'sms_to':[sms_to],'sms_status_type':[r.status_code],'sms_json_response':[str(r.json())]}
#             else:
#                 sms_dict = {'sms_text': [sms_text], 'sms_type': [sms_type], 'sms_to': [sms_to],'sms_status_type': [r.status_code], 'sms_json_response': ['{}']}
#             new_sms_df = pd.DataFrame(sms_dict)
#             engine = connections('prod_db_write')
#             new_sms_df.loc[0, 'sms_text'] = sanitise_for_sql({'message': new_sms_df.loc[0, 'sms_text']}).get('message', '')
#             new_sms_df.to_sql(name = 'sms_log', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
#             return None
#         except:
#             print('SMS API error',flush=True)
#             mailer.send_exception_mail()
#             return None

def send_raven_v1(template_name,sms_to=919582148040,send=True,body_parameters={}):
    key = raven_key
    url = raven_sms_url
    data ={"event" : template_name,"user":{"mobile":sms_to}, "data": body_parameters}
    # data.update(body_parameters)
    headers = {'Content-type': 'application/json', 'Authorization': key}
    if ((send)&(server_type!='local')):
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers)
            if(r.status_code==200):
                sms_dict = {'sms_text':["Text sent. Check Raven Logs"],'sms_type':["Transactional"],'sms_to':[sms_to],'sms_status_type':[r.status_code],'sms_json_response':[str(r.json())]}
            else:
                sms_dict = {'sms_text': ["Failed to send SMS. Check Raven Logs"], 'sms_type': ["Transactional"], 'sms_to': [sms_to],'sms_status_type': [r.status_code], 'sms_json_response': [str(r.json())]}
            new_sms_df = pd.DataFrame(sms_dict)
            engine = connections('prod_db_write')
            new_sms_df.loc[0, 'sms_text'] = sanitise_for_sql({'message': new_sms_df.loc[0, 'sms_text']}).get('message', '')
            new_sms_df.to_sql(name = 'sms_log', con = engine, schema='covidsos', if_exists='append', index = False,index_label=None)
            return None
        except:
            print('SMS API error',flush=True)
            mailer.send_exception_mail()
            return None


# In[ ]:



def send_otp(otp_to):
    # if server_type=='local':
    #     return 'server_type is local', False
    try:
        r = requests.post(otp_url, params={"template_id":otp_template_id,"authkey": sms_key, "mobile": f'91{otp_to}'})
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
        r = requests.post(url, params={"template_id":otp_template_id,"authkey": sms_key, "mobile": f'91{otp_to}'})
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


def update_request_status(r_uuid,status, status_message, volunteer_id):
    reqStatus = status
    if status == 'completed externally':
        reqStatus, status_message = 'completed', 'completed externally'
    if status == 'cancelled':
        reqStatus = 'verified'
    status_message = sanitise_for_sql({'message': status_message}).get('message', '')
    request_update_query = f""" insert into request_updates (request_uuid, status, status_message,v_id) values ('{r_uuid}', '{status}', '{status_message}','{volunteer_id}'); """
    # update request_updates
    try:
        write_query(request_update_query,'prod_db_write')
    except:
        mailer.send_exception_mail()
        return 'Failed to add request update', False
    update_requests_db({'uuid':r_uuid},{'status': reqStatus})
    # update request_matching
    if status == 'cancelled':
        r_id_query = f""" select id from requests where uuid = '{r_uuid}'"""
        r_id = pd.read_sql(r_id_query, connections('prod_db_read')).loc[0, 'id']
        request_matching_query = f""" update request_matching set is_active=False where request_id={r_id}"""
        try:
            write_query(request_matching_query,'prod_db_write')
        except:
            mailer.send_exception_mail()
            return 'Failed to cancel request matching', False
    return 'Updated request status', True


def save_request_sms_url(request_uuid, url_type, url):
    try:
        url = sanitise_for_sql({'message': url[:1000]}).get('message', '')
        query = f"""insert into request_sms_urls (r_uuid, url_type, url) values ('{request_uuid}', '{url_type}', '{url}');"""
        write_query(query,'prod_db_write')
        return True
    except:
        print(url,flush=True)
        mailer.send_exception_mail()
        return False
