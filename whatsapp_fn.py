#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import time
from lib.redis import redis

from database_entry import add_message
from settings import server_type, whatsapp_api_url, whatsapp_api_password,auth_code,namespace,whatsapp_temp_1,bot_number, stale_whatsapp_message_threshold
from database_entry import send_sms,update_volunteers_db,update_requests_db,update_users_db
from flask import Flask,request
from message_templates import a,b,c,c1,c2,inv,whatsapp_temp_1_message
import pandas as pd
from connections import connections
from data_fetching import get_moderator_list,accept_request_page,volunteer_data_by_mob
import datetime as dt
from lib.redis import redis
# In[ ]:

app = Flask(__name__)




# In[ ]:


#Where to get this from
def get_auth_key():
    url=whatsapp_api_url+"/v1/users/login"
    payload = {"new_password": whatsapp_api_password}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic <base64(username:password)>',
        'Authorization': auth_code
            }
    response = requests.request("POST", url, headers=headers, data = json.dumps(payload),verify=False)
    rs=response.text
    json_data=json.loads(rs)
    return json_data["users"][0]["token"]


# In[ ]:

def check_contact(mob_number,table='volunteers',url=whatsapp_api_url):
    try:
        url = url +"/v1/contacts"
        authkey = get_auth_key()
        data = {"blocking":"wait","contacts": ["{mob_number}".format(mob_number=mob_number)],"force_check":True}
        headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+authkey}
        response = requests.request("POST", url, headers=headers, data=json.dumps(data)).json()
        if (response.get("errors") is None):
            print('Contact Verification API Run successfully',flush=True)
            print('data sent was', data,flush=True)
            print('response json is ', response,flush=True)
            if(response.get("contacts")[0].get("status") == 'valid'):
                wa_id = response.get("contacts")[0].get("wa_id")
                print('Valid WhatsApp contact',flush=True)
            elif(response.get("contacts")[0].get("status") == 'processing'):
                wa_id = 'processing'
                print('WhatsApp API processing',flush=True)
            else:
                wa_id = 'SMS'
                print('Invalid WhatsApp contact',flush=True)
            print(wa_id)
            where_dict = {'mob_number':mob_number[3:]}
            set_dict = {'whatsapp_id':wa_id}
            if(table=='volunteers'):
                res = update_volunteers_db(where_dict, set_dict)
            elif(table=='requests'):
                res = update_requests_db(where_dict, set_dict)
            elif(table=='users'):
                res = update_users_db(where_dict, set_dict)
        else:
            print('Error in the API Call',flush=True)
            print('data sent was', data,flush=True)
            print('response json is ', response,flush=True)
        return None
    except Exception as e:
        print('error in check_contact', e,flush=True)
        return None

def send_whatsapp_message(url,to,message,preview_url=False):
    add_message(to[2:], bot_number, to[2:], message, "text", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    ##print("Inside message")
    data = {"to": to,"type": "text","recipient_type":"individual","text":{"body":message},"preview_url":preview_url}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+authkey}
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers,verify = False).json()
        print("message sent",flush=True)
        print(response,flush=True)
        if(response.get("errors") is None):
            return True
        else:
            print('data is ', data,flush=True)
            print('response is ', response,flush=True)
            return False
    except Exception as e:
        print(e)
        return False


def send_whatsapp_message_image(url,to,media_link,media_caption):
    add_message(to[2:], bot_number, to[2:], media_link, "image", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    ##print("Inside message")
    data = {"to": to,"type": "image","recipient_type":"individual","image": {"provider": {"name": "covidsos"},"link": "<Link to Image, https>","caption": "<Media Caption>"}}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+authkey}
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers,verify = False).json()
        print("message sent",flush=True)
        if (response.get("errors") is None):
            return True
        return False
    except Exception as e:
        print(e,flush=True)
        return False


def send_whatsapp_template_message(url,to,namespace,element_name,message_template,body_parameter):
    message = message_template.format(body_parameter)
    add_message(to[2:], bot_number, to[2:], message, "text", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    print("Inside message",flush=True)
    data = {"to": to, "type": "hsm", "hsm": {"namespace": namespace, "element_name": element_name,
                                             "language": {"policy": "deterministic",
                                                          "code": "en"},
                                             "localizable_params": body_parameter}}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+ authkey}
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers, verify = False).json()
        print(response,flush=True)
        if response.get("errors") is None:
            print("WhatsApp message sent",flush=True)
            return True
        else:
            print("message {message} not sent, received response {txt}".format(message=message, txt=str(response.text)),flush=True)
            return False
    except Exception as e:
        print("message {message} not sent, received exception {exception}".format(message=message, exception=str(e)),flush=True)
        return False


def send_request_template(uuid,sms_text,mob_number):
    try:
        v_df = volunteer_data_by_mob(mob_number)
        if(v_df.shape[0]==0):
            return {'status':False, 'string_response':'Volunteer number incorrect'}
        if (pd.isna(v_df.loc[0, 'whatsapp_id']) or v_df.loc[0, 'whatsapp_id']=='processing'):
            check_contact( "+" + str(91) + str(mob_number),'volunteers', whatsapp_api_url)
            v_df = volunteer_data_by_mob(mob_number)
        df = accept_request_page(uuid)
        v_name = v_df.loc[0,'name']
        requestor_name = df.loc[0,'name']
        Address = df.loc[0,'request_address']
        urgency_status = 'This is an urgent request!' if df.loc[0,'urgent']=='yes' else 'This request needs support in 1-2 days'
        reason = df.loc[0,'why']
        requirement = df.loc[0,'what']
        if(server_type=='prod'):
            acceptance_link = 'https://covidsos.org/accept/'+str(uuid)
            v_name = "from CovidSOS"
        else:
            acceptance_link = 'https://stg.covidsos.org/accept/'+str(uuid)
            v_name = " Test "
        financial_assistance_status = 'This help-seeker cannot afford to pay.' if df.loc[0,'financial_assistance']==1 else 'This help-seeker can afford to pay for items delivered.'
        body_parameters =[{"default":v_name}, {"default": requestor_name}, {"default": Address}, {"default": urgency_status}, {
            "default": requestor_name}, {"default": reason},
                          {"default": requestor_name}, {"default": requirement}, {"default": financial_assistance_status},{"default":acceptance_link}]
        message = whatsapp_temp_1_message.format(v_name = v_name, requestor_name = requestor_name, Address=Address,
                                                 urgency_status=urgency_status,reason=reason,requirement=requirement,
                                                 financial_assistance_status=financial_assistance_status,
                                                 acceptance_link=acceptance_link)
        print(message,flush=True)
        m_num = v_df.loc[0,'whatsapp_id']
        print(m_num,flush=True)
        if ((m_num=='SMS') or (send_whatsapp_template_message(whatsapp_api_url, m_num, namespace, whatsapp_temp_1, message,
                                              body_parameters)==False)):
            send_sms(sms_text, int(mob_number))
            print('SMS sent',flush=True)
        return {'status':True, 'string_response':'Message Sent'}
    except Exception as e:
        print("Exception in sending message {e}".format(e=e),flush=True)
        return {'status':False, 'string_response':'Error occurred'}


def send_moderator_msg(mob_number,message,preview_url=False):
    print(message,flush=True)
    m_num = str(91)+str(mob_number)
    print(m_num,flush=True)
    if has_user_replied(m_num):
        try:
            check_contact("+" + str(m_num), 'users')
            wa_msg = send_whatsapp_message(whatsapp_api_url,m_num,message,preview_url)
            if wa_msg:
                return {'status': True, 'string_response': 'WhatsApp Message Sent'}
            else:
                send_sms(message,int(mob_number))
                return {'status': True, 'string_response': 'SMS Sent'}
        except Exception as e:
            send_sms(message, int(mob_number))
            print("Exception in sending message {e}".format(e=e),flush=True)
            return {'status': False, 'string_response': 'Error in send_moderator_msg'}
    else:
        print("User has not replied since last 24 hours; sending message {message} to {number}".format(message=message, number = m_num))
        send_sms(message,int(mob_number))
        return {'status': True, 'string_response': 'SMS Sent'}

# In[ ]:

#TODO Add function to save chats to db
#TODO Add function to create group with all users as per list of active moderators in user_table (get_moderator_list in data_fetching.py)
#TODO Add function to send message to that group and read whatever is received
# x =send_whatsapp_message(whatsapp_api_url,'919582148040','Testing message')


# In[ ]:

def get_user_replied_marker(wa_id):
    return "wa_id_{wa_id}_replied_marker"

def set_user_replied_marker(whatsapp_id):
    # setting limit to 1 day as per whatsapp rules
    redis.set(get_user_replied_marker(whatsapp_id), 1, ex=24*3600)

def has_user_replied(whatsapp_id):
    return redis.get(get_user_replied_marker(whatsapp_id)) != None


def get_stale_marker_redis_key(wa_id):
    return "waid_{wa_id}_stale_marker".format(wa_id=wa_id)

def check_mesage_to_number_already_sent(whatsapp_id):
    key_val = redis.get(get_stale_marker_redis_key(whatsapp_id))
    return key_val != None

def mark_number_as_processed_for_stale_message(whatsapp_id):
    # assuming that the server proceessed all messages in 1 hour
    redis.set(get_stale_marker_redis_key(whatsapp_id), 1, ex=3600)
    
def process_whatsapp_received_text_message(message):
    body = str(message.get("text").get("body"))
    whatsapp_id = str(message.get('from'))
    add_message(whatsapp_id, whatsapp_id, bot_number, body, "text", "whatsapp", "incoming")

    current_time = int(time.time())
    timestamp = int(message.get('timestamp', current_time))
    whatsapp_id = str(message.get('from'))
    if (current_time - timestamp > stale_whatsapp_message_threshold): 
        if check_mesage_to_number_already_sent(whatsapp_id):
            print("Message to whatsapp_id {wa_id} already processed skipping".format(wa_id=whatsapp_id))
            return
        else:
            mark_number_as_processed_for_stale_message(whatsapp_id)

    #Storing Message, Media or Location
    #elif (response.get("messages")[0].get("type")=='image'):

    #Replace with functions from data_fetching

    ## query for volunteer
    checkState = """SELECT name, timestamp, id, whatsapp_id from volunteers where mob_number='{mob_number}'""".format(mob_number=int(whatsapp_id[2:]))
    print(checkState)
    records_a = pd.read_sql(checkState, connections('prod_db_read'))
    ## query for requester
    checkState = """SELECT name, timestamp, id, whatsapp_id from requests where mob_number='{mob_number}'""".format(mob_number=whatsapp_id[2:])
    records_b = pd.read_sql(checkState, connections('prod_db_read'))

    ## check for volunteer
    if records_a.shape[0]>0:
        if (records_a.loc[0, 'whatsapp_id'] != whatsapp_id):
            check_contact("+" + str(whatsapp_id), 'volunteers')
        name = records_a.loc[0,'name']
        send_whatsapp_message(whatsapp_api_url, whatsapp_id, a.format(v_name=name))

    ## check for requester
    elif records_b.shape[0]>0:
        if (records_b.loc[0, 'whatsapp_id'] != whatsapp_id):
            check_contact("+" + str(whatsapp_id), 'requests')
        name = records_b.loc[0,'name']
        send_whatsapp_message(whatsapp_api_url, whatsapp_id, b.format(r_name=name))

    ## if new user
    else:
        if body != '1' and body != '2':
            send_whatsapp_message(whatsapp_api_url, whatsapp_id, c)
        if body == '1':
            send_whatsapp_message(whatsapp_api_url, whatsapp_id, c1)
        if body == '2':
            send_whatsapp_message(whatsapp_api_url, whatsapp_id, c2)

    print('\n The whatsapp ID is ' + whatsapp_id + '\n',flush=True)

@app.route('/', methods=['POST', 'GET'])
def Get_Message():
    response = request.json

    for message in response.get('messages', []):
        whatsapp_id = str(message.get('from'))
        set_user_replied_marker(whatsapp_id)
        if message.get('text', False):
            print(response, flush=True)
            process_whatsapp_received_text_message(message)
    return "ok"

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=4000)