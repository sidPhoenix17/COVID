#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
from settings import server_type, whatsapp_api_url, whatsapp_api_password,auth_code
from flask import Flask,request
from message_templates import a,a1,a2,b,b1,b2,c,c1,c2,mod_wait,inv
import pandas as pd
from connections import connections
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

def send_whatsapp_message_image(url,to,media_link,media_caption):
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
    try:
        frm = str(response["messages"][0]["from"])
        text = str(response["messages"][0]["text"]["body"])
        ## query for volunteer
        checkState = """SELECT name, timestamp, id from volunteers where mob_number='{mob_number}'""".format(mob_number=frm)
        records_a = pd.read_sql(checkState, connections('prod_db_read'))

        ## query for requester
        checkState = """SELECT name, timestamp, id from requests where mob_number='{mob_number}'""".format(mob_number=frm)
        records_b = pd.read_sql(checkState, connections('prod_db_read'))

        ## check for volunteer
        if records_a.shape[0]>0:
            hist = 'v'
            name = records_a.loc[0,'name']
            if text != '1' and text != '2' and text != 'a' and text != 'A':
                send_whatsapp_message(whatsapp_api_url, frm, a.format(v_name=name))

            if text == '1':
                timestamp = str(records_a.loc[0,'timestamp'])
                v_id = str(records_a.loc[0,'id'])
                query = """Select r.name as `r_name`,r.uuid as `uuid`,
                            rv.where as `where`, rv.what as `what`, rv.why as `why`, rm.timestamp as `assignment_time`
                            from requests r
                        left join request_verification rv on rv.r_id=r.id
                        left join request_matching rm on rm.request_id=r.id
                        left join volunteers v on v.id=rm.volunteer_id
                        where rm.`is_active`=True and v.`id`='{v_id}' and r.`status`='matched'
                        ORDER BY rm.timestamp DESC LIMIT 1 """.format(v_id=v_id)
                df = pd.read_sql(query, connections('prod_db_read'))
                send_whatsapp_message(whatsapp_api_url, frm,
                                      a1.format(v_name=name, r_name=df.loc[0,'r_name'], adrs=df.loc[0,'where'],
                                                reason=df.loc[0,'why'], requirement=df.loc[0,'what']))
            if text == '2':
                send_whatsapp_message(whatsapp_api_url, frm, a2.format(name))
            if text == 'a' or text == 'A':
                send_whatsapp_message(whatsapp_api_url, frm, mod_wait)


        ## check for requester
        elif records_b.shape[0]>0:
            hist = 'r'
            name = records_b.loc[0,'name']
            if text != '1' and text != '2' and text != 'a' and text != 'A':
                send_whatsapp_message(whatsapp_api_url, frm, b.format(r_name=name))

            if text == '1':
                name =records_b.loc[0,'name']
                timestamp = dt.datetime.strftime(records_b.loc[0,'timestamp'],'%a, %d %b %y, %I:%M%p %Z')
                r_id = records_b.loc[0,'id']
                query = """Select v.name, v.mob_number from request_matching rm 
                left join volunteers v on v.id=rm.v_id 
                where rm.r_id='{r_id}' and rm.is_active=True""".format(r_id=r_id)
                df = pd.read_sql(query, connections('prod_db_read'))
                v_name = df.loc[0,'name']

                send_whatsapp_message(whatsapp_api_url, frm, b1.format(r_name=name,date_time= timestamp,v_name= v_name,link= "http://wa.me/918618948661"))
            if text == '2':
                send_whatsapp_message(whatsapp_api_url, frm, b2.format(r_name=name))
            if text == 'a' or text == 'A':
                send_whatsapp_message(whatsapp_api_url, frm, mod_wait)

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

    except Exception as e:

        print(e)
    return ""


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=4000)