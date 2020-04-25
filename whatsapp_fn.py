from flask import Flask
from flask import jsonify
from flask import request
import requests
import http.client
import json
from datetime import datetime
import urllib3
import pymysql

#from settings import server_type, whatsapp_api_url, whatsapp_api_password,auth_code

whatsapp_api_url = "https://100.24.50.36:9090"
whatsapp_api_password = "Khairnar@123"

app = Flask(__name__)


#Where to get this from
def get_auth_key():
    url=whatsapp_api_url+"/v1/users/login"
    payload = {"new_password": whatsapp_api_password}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic <base64(username:password)>',
        'Authorization': 'Basic YWRtaW46S2hhaXJuYXJAMTIz'
            }
    response = requests.request("POST", url, headers=headers, data = json.dumps(payload),verify=False)
    rs=response.text
    json_data=json.loads(rs)
    return json_data["users"][0]["token"]

authkey=get_auth_key()


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


aws_host ="stg.covidsos.org"
usr = "uphar"
pas = "UpH4R@c0VId"
db = "covidsos"

@app.route('/', methods=['POST','GET'])
def Get_Message():
    now = str(datetime.now().date())
    now_time = str(datetime.now())

    print("_______________________________________________________________________")

    print("entered")
    cnt=0
    response = request.json
    print(response)
    
    cnx = pymysql.connect(user=usr, max_allowed_packet= 1073741824, password=pas, host=aws_host, database=db)
    
    
    try:
        frm = str(response["messages"][0]["from"])
        text=str(response["messages"][0]["text"]["body"])
        
        checkState="SELECT name from covidsos.volunteers where mob_number='"+frm[2:]+"'"
        cursor = cnx.cursor()
        cursor.execute(checkState)
        records = cursor.fetchone()
        
        if records == None:
            send_whatsapp_message(whatsapp_api_url,frm,'not volunteer')
        else:
            name = list(records)[0]
            send_whatsapp_message(whatsapp_api_url,frm,name)

        print('\n'+frm+'\n')


        
    except Exception as e:
        
        print(e)

    print("****************************************************************************")

    return ""

if __name__ == '__main__':
    app.debug=True
    app.run(host = '0.0.0.0', port=4000)

        

        