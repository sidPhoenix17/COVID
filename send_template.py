import requests
import sys

url = "https://100.24.50.36:9090/"
url_template = "https://100.24.50.36:9090/v1/messages/"
url_register = "https://100.24.50.36:9090/v1/contacts/"
to = "919130121847" #sys.argv[1]

def update_authkey(urls):
    url= urls+"v1/users/login"
    payload = "{\n\t\"new_password\": \"Khairnar@123\"\n}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic <base64(username:password)>',
        'Authorization': 'Basic YWRtaW46S2hhaXJuYXJAMTIz'
            }
    response = requests.request("POST", url, headers=headers, data = payload,verify=False)
    rs=response.text
    json_data=json.loads(rs)
    return json_data["users"][0]["token"]

authkey=update_authkey(url)

## register contact

payload = "{\n   \"blocking\": \"wait\",\n   \"contacts\": [\""+to[2:]+"\"] \n}"
print(payload)
headers = {
    'Content-Type': "application/json",
    'Authorization': "Bearer "+authkey,
    'cache-control': "no-cache",
    'Postman-Token': "d1e7e7ca-c958-42f9-acbd-06055f599a32"
    }

response = requests.request("POST", url_register, data=payload, headers=headers, verify=False)
print(response.text)




## send template

payload = "{\n\t\"to\": \""+to+"\",\n\t\"type\": \"hsm\",\n\t\"recipient_type\": \"individual\",\n\t\"hsm\": {\n\t\t\"namespace\": \"10aac1cc_58ce_4275_8374_9b0ffd4b9de1\",\n    \t\"element_name\": \"ktpl_welcome\",\n    \t\"language\": {\n    \t\t\"policy\": \"deterministic\",\n    \t\t\"code\": \"en\"\n    \t},\n    \t\"localizable_params\": [{\"default\":\"Bridgestone\"},{\"default\":\"invoice\"}]\n\t}\n}\n"
print(payload)

headers = {
    'Content-Type': "application/json",
    'Authorization': "Bearer "+authkey,
    'User-Agent': "PostmanRuntime/7.20.1",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Postman-Token': "43300725-c894-4a55-93d2-503734d532f1,658105e3-ba15-4797-876a-f21bb97bf1e9",
    'Host': "100.24.50.36:9090",
    'Accept-Encoding': "gzip, deflate",
    'Content-Length': "321",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
    }

response = requests.request("POST", url_template, data=payload, headers=headers, verify=False)

print(response.text)
