#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json

from database_entry import add_message
from settings import server_type, whatsapp_api_url, whatsapp_api_password,auth_code,namespace,whatsapp_temp_1,bot_number
from flask import Flask,request
from message_templates import a,b,c,c1,c2,inv,whatsapp_temp_1_message
import pandas as pd
from connections import connections
from data_fetching import get_moderator_list,accept_request_page,volunteer_data_by_mob
import datetime as dt
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


def send_whatsapp_message(url,to,message,preview_url=False):
    add_message(to[2:], bot_number, to[2:], message, "text", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    ##print("Inside message")
    data = {"to": to,"type": "text","recipient_type":"individual","text":{"body":message},"preview_url":preview_url}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+authkey}
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers,verify = False)
        print("message sent")
    except Exception as e:
        print(e)
    return response

def send_whatsapp_template_message(url,to,namespace,element_name,message_template,body_parameter):
    message = message_template.format(body_parameter)
    add_message(to[2:], bot_number, to[2:], message, "text", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    print("Inside message")
    data = {"to": to, "type": "hsm", "hsm": {"namespace": namespace, "element_name": element_name,
                                             "language": {"policy": "deterministic",
                                                          "code": "en"},
                                             "localizable_params": body_parameter}}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+ authkey}
    print(json.dumps(data))
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers, verify = False)
        print("message sent")
    except Exception as e:
        print(e)
    return response

# @app.route('/testing', methods=['POST'])
def send_sample_template(uuid):
    # uuid = request.form.get('uuid')
    l_mob = [9560488236]
    for i in l_mob:
        v_df = volunteer_data_by_mob(i)
        df = accept_request_page(uuid)
        v_name = v_df.loc[0,'name']
        requestor_name = df.loc[0,'name']
        Address = df.loc[0,'request_address']
        urgency_status = 'This is an urgent request!' if df.loc[0,'urgent']=='yes' else 'This request needs support in 24-48 hours'
        reason = df.loc[0,'why']
        requirement = df.loc[0,'what']
        financial_assistance_status = 'This request involves monetary support' if df.loc[0,'financial_assistance']==1 else 'This request does not involve monetary support'
        acceptance_link = 'https://covidsos.org/accept/'+str(uuid)
        body_parameters =[{"default":v_name}, {"default": requestor_name}, {"default": Address}, {"default": urgency_status}, {
            "default": requestor_name}, {"default": reason},
        {"default": requestor_name}, {"default": requirement}, {"default": financial_assistance_status},{"default":acceptance_link}]
        message = whatsapp_temp_1_message.format(v_name = v_name, requestor_name = requestor_name, Address=Address,
                                                urgency_status=urgency_status,reason=reason,requirement=requirement,
                                                 financial_assistance_status=financial_assistance_status,
                                                acceptance_link=acceptance_link)
        print(message)
        m_num = str(91)+str(i)
        print(m_num)
        response = send_whatsapp_template_message(whatsapp_api_url,m_num,namespace,whatsapp_temp_1,message,body_parameters)
        print(response)
        return response





def send_whatsapp_message_image(url,to,media_link,media_caption):
    add_message(to[2:], bot_number, to[2:], media_link, "image", "whatsapp", "outgoing")
    url = url+'/v1/messages'
    authkey = get_auth_key()
    ##print("Inside message")
    data = {"to": to,"type": "image","recipient_type":"individual","image": {"provider": {"name": "covidsos"},"link": "<Link to Image, https>","caption": "<Media Caption>"}}
    headers = {'Content-type': 'application/json', 'Authorization': "Bearer "+authkey}
    try:
        response = requests.request("POST", url, data=json.dumps(data), headers=headers,verify = False)
        print("message sent")
        if(str(response)=='<Response [201]>'):
            output = {'Response':json.loads(response.text)['messages'],'status':True,'string_response':'Successfully sent'}
    except Exception as e:
        output = {'Response':{},'status':False,'string_response':'Failure'}
        print(e)
    return output


# In[ ]:

#TODO Add function to save chats to db
#TODO Add function to create group with all users as per list of active moderators in user_table (get_moderator_list in data_fetching.py)
#TODO Add function to send message to that group and read whatever is received
# x =send_whatsapp_message(whatsapp_api_url,'919582148040','Testing message')


# In[ ]:


@app.route('/', methods=['POST', 'GET'])
def Get_Message():
    # now = str(dt.datetime.now().date())
    # now_time = str(dt.datetime.now())
    response = request.json
    print(response)

    frm = str(response["messages"][0]["from"])
    text = str(response["messages"][0]["text"]["body"])
    ## query for volunteer
    checkState = """SELECT name, timestamp, id from volunteers where mob_number='{mob_number}'""".format(mob_number=frm[2:])
    records_a = pd.read_sql(checkState, connections('prod_db_read'))

    ## query for requester
    checkState = """SELECT name, timestamp, id from requests where mob_number='{mob_number}'""".format(mob_number=frm[2:])
    records_b = pd.read_sql(checkState, connections('prod_db_read'))

    ## check for volunteer
    if records_a.shape[0]>0:
        name = records_a.loc[0,'name']
        add_message(frm, frm, bot_number, text, "text", "whatsapp", "incoming")
        send_whatsapp_message(whatsapp_api_url, frm, a.format(v_name=name))

    ## check for requester
    elif records_b.shape[0]>0:
        name = records_b.loc[0,'name']
        add_message(frm, frm, bot_number, text, "text", "whatsapp", "incoming")
        send_whatsapp_message(whatsapp_api_url, frm, b.format(r_name=name))
    ## if new user
    else:
        print(text)
        if text != '1' and text != '2':
            send_whatsapp_message(whatsapp_api_url, frm, c)
        if text == '1':
            send_whatsapp_message(whatsapp_api_url, frm, c1)
        if text == '2':
            send_whatsapp_message(whatsapp_api_url, frm, c2)

    print('\n' + frm + '\n')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=4000)