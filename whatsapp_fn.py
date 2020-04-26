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


a = "Hi {}, thank you for messaging COVIDSOS. \n\nPlease click 1 to know requests assigned to you.\n\nPlease click 2 to help someone."
b = "Hi {}, thank you for messaging COVIDSOS. \n\nPlease click 1 to know status of your latest request. \n\nPlease click 2 to submit a new request."
c = "Hi, thank you for messaging COVIDSOS. \n\nPlease click 1 to register as a volunteer. \n\nPlease click 2 if you need help"

mod_wait = "Our team will reach out to you shortly"


a1 = "Hi {v_name}, \n{r_Name} in your area (adrs}) requires help! \n\nWhy does {r_name} need help?\n{reason} \n\nHow can you help {r_name}? \n{requirement} \n\nThis is a verified request received via www.covidsos.org and it would be great if you can help.!🙂\n\nIf you can help, please click: {acceptance_link}\n\nIf you have any further concerns regarding this request, please click A."

a2 = "Dear {}. Thank you for stepping up in times of need. We will reach out to you if anyone near you needs help. \n\nIn the meanwhile, here are the list of pending requests www.covidsos.org/pending-requests"


b1 = "Dear {r_name}, with regards to your request raised on {date_time}, volunteer {v_name} has agreed to assist you. He/She shall reach out to you shortly. In case of any issues, kindly click here {link} \nIf you have any further concerns regarding this request, please click A."

b2 = "To submit a new request for help, please click here → www.covidsos.org/"


c1 ="Dear user. Thank you for stepping up in times of need. It is easy to now help someone. \nJust register on www.covidsos.org as a volunteer. \n\nWe will reach out to you if anyone near you needs help. "

c2 = "To submit a new request for help, please click here → www.covidsos.org/"


inv = "Dear user, kindly enter a valid response. \nYou can reach out to us by clicking here. \nwww.covidsos.org/contact-us"


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
    print(data)
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
    data = {"to": to,"type": "image","recipient_type":"individual","image": {"provider": {"name": "covidsos"},"link": "<Link to Image,   https>","caption": "<Media Caption>"}}
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
        
        ## query for volunteer
        checkState="SELECT name, timestamp, id from covidsos.volunteers where mob_number='"+frm[2:]+"'"
        cursor_a = cnx.cursor()
        cursor_a.execute(checkState)
        records_a = cursor_a.fetchone()
       
            
        ## query for requester
        checkState="SELECT name, timestamp, id from covidsos.requests where mob_number='"+frm[2:]+"'"
        cursor_b = cnx.cursor()
        cursor_b.execute(checkState)
        records_b = cursor_b.fetchone()
        
        
        ## check for volunteer
        if records_a != None:
            hist = 'v'
            name = list(records_a)[0]
                
            if text !='1' and text != '2' and text != 'a' and text != 'A':
                send_whatsapp_message(whatsapp_api_url,frm,a.format(name))
            
            if text == '1':
                
                timestamp = str(list(records_a)[1])
                v_id = str(list(records_b)[2])
                
                checkState="SELECT r.name from covidsos.requests as r inner join covidsos.request_matching as m  where r.id = (Select request_id from covidsos.request_matching where volunteer_id = '{}' ORDER BY timestamp DESC LIMIT 1 )".format(V_id)
                cursor = cnx.cursor()
                cursor.execute(checkState)
                records = cursor_a.fetchone()
                re_name = str(list(records)[0])
                
                checkState="SELECT r.why, r.what, r.where from covidsos.request_verification as r inner join covidsos.request_matching as m  where r.id = (Select request_id from covidsos.request_matching where volunteer_id = '{}' ORDER BY timestamp DESC LIMIT 1 ) ORDER BY timestamp DESC LIMIT 1".format(V_id)
                cursor = cnx.cursor()
                cursor.execute(checkState)
                records = cursor_a.fetchone()
                why = str(list(records)[0])
                what = str(list(records)[1])
                where = str(list(records)[2])
                
                
                send_whatsapp_message(whatsapp_api_url,frm,a1.format(v_name=name, r_name=re_name, adrs=where, reason=why,requirement=what,acceptance_link="abc.com"))
            if text == '2':
                send_whatsapp_message(whatsapp_api_url,frm,a2.format(name))
            if text == 'a' or text == 'A':
                send_whatsapp_message(whatsapp_api_url,frm,mod_wait)
            
        
        ## check for requester
        elif records_b != None:
            hist = 'r'
            name = list(records_b)[0]
            if text !='1' and text != '2' and text != 'a' and text != 'A':
                send_whatsapp_message(whatsapp_api_url,frm,b.format(name))
            
            if text == '1':
                
                name = list(records_b)[0]
                timestamp = str(list(records_b)[1])
                r_id = str(list(records_b)[2])
                
                checkState="SELECT v.name from covidsos.volunteers as v inner join covidsos.request_matching as m  where v.id = (Select volunteer_id from covidsos.request_matching where request_id = '{}' ORDER BY timestamp DESC LIMIT 1 )".format(r_id)
                cursor = cnx.cursor()
                cursor.execute(checkState)
                records = cursor_a.fetchone()
                v_name = str(list(records)[0])
                
                
                send_whatsapp_message(whatsapp_api_url,frm,b1.format(name, timestamp, v_name,"abc.com"))
            if text == '2':
                send_whatsapp_message(whatsapp_api_url,frm,b2.format(name))
            if text == 'a' or text == 'A':
                send_whatsapp_message(whatsapp_api_url,frm,mod_wait)
            
            
         
        ## if new user
        else:
            print(text)
            if text !='1' and text != '2':
                send_whatsapp_message(whatsapp_api_url,frm,c)
            
            if text == '1':
                send_whatsapp_message(whatsapp_api_url,frm,c1)
            if text == '2':
                send_whatsapp_message(whatsapp_api_url,frm,c2)

        print('\n'+frm+'\n')


        
    except Exception as e:
        
        print(e)

    print("****************************************************************************")
    cnx.close()
    return ""

if __name__ == '__main__':
    app.debug=True
    app.run(host = '0.0.0.0', port=4000)

        

        