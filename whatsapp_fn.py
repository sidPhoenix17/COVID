#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
from settings import server_type, whatsapp_api_url, whatsapp_api_password,auth_code


# In[ ]:





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



# x =send_whatsapp_message(whatsapp_api_url,'919582148040','Testing message')


# In[ ]:





# In[ ]:




