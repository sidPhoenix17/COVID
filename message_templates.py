
import urllib
import requests
from settings import server_type

if(server_type=='prod'):
    key_word = " "
    url_start = "https://covidsos.org/"
else:
    key_word = "TEST"
    url_start = "https://stg.covidsos.org/"

def url_shortener_fn(input_url):
    url = 'http://tinyurl.com/api-create.php'
    params = {'url':input_url}
    request = requests.get(url=url,params=params)
    if(request.text=='Error'):
        return input_url
    else:
        return request.text

otp_template_id = "60797630bbc8476bc6229714"
# otp_template = {"flow_id": "60797630bbc8476bc6229714", "template": "COVIDSOS - Your OTP to access user info is {OTP}"}
# request_closed_req_2 = {"flow_id":" ","template":"COVIDSOS ##key## Your request has been ##status## as per the feedback. If you have any further requests, click ##link##"}
# rejected_request_to_requestor = {"flow_id":" ","template":"COVIDSOS ##key## Your request has been cancelled/rejected. If you still need help, please submit the request again."}
# request_closed_requestor = {"flow_id":" ","template":"COVIDSOS ##key## Your request has been ##status## as per the feedback from volunteer. If you have any further requests, click ##link##"}
# request_closed_vol_2 = {"flow_id":" ","template":"##key## Thank you. Request assigned to you has been ##status## by the ##user_name##, COVIDSOS. Every volunteer is a hero. Refer a friend by clicking here ##link##"}
# request_closed_vol = {"flow_id":" ","template":"COVIDSOS ##key## Thank you.This request has been ##status##. Every volunteer is a hero. Refer a friend by clicking here ##link##"}
# existing_user_registration = {"flow_id":" ","template":"You are already registered with COVIDSOS ##key##. Support us by asking a friend to volunteer. Click here: ##link##"}
# accepted_request_requestor = {"flow_id":" ","template":"COVIDSOS ##key## A volunteer has accepted to help you. Click here to speak to us: ##link##"}
# request_verification_moderator = {"flow_id":" ","template":"COVIDSOS ##key## New query received from ##source##. Verify lead by clicking here: ##urlstart##verify/##uuid##"}
# request_received = {"flow_id":" ","template":"COVIDSOS ##key## ##name##, we have received your request via ##source##. We will call you soon. If urgent, please click ##link##"}



def url_retriever(template_name):
    if(template_name=="new_request_sms"):
        url = "https://covidsos.org/how-it-works"

    elif((template_name=="a_existing_user_registration")or(template_name=="a_new_user_registration")):
        url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")

    elif(template_name=="a_accepted_request_vol"):

        url = "https://wa.me/918618948661?text=" + urllib.parse.quote_plus("I have accepted a request and have a query")

    elif(template_name=="a_accepted_request_requestor"):
        url = "https://wa.me/918618948661?text=" + urllib.parse.quote_plus("My request is accepted and I have a query")

    elif(template_name=="a_verified_req"):
        url = "https://covidsos.org/how-it-works"

    elif((template_name=="a_request_closed_vol") or (template_name=="a_request_closed_vol_2")):
        url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")

    elif(template_name=="a_request_closed_req_2"):
        url = "https://covidsos.org/"

    link = url_shortener_fn(url)
    return link



#New User
# url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("I have registered!")
# link = url_shortener_fn(url)
url = "https://api.whatsapp.com/send?text="+urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")
link = url_shortener_fn(url)
new_reg_sms = key_word+" Thank you for your kindness. Support us by asking a friend to volunteer. Click here: "+ link
new_reg_sms_dict = {'flow_id':'5ef77c61d6fc0575c821283c','message': key_word + " Thank you for your kindness. Support us by asking a friend to volunteer. Click here: " + link}
new_reg_whatsapp = "Thank you for registering as a volunteer with COVIDSOS. We will reach out to you if anyone near your location needs help. Please reach out to wa.me/918618948661 to know how you can help us."
new_reg_whatsapp_img = {'media_link':'cdcdscdc311','caption':'Share this with your friends and family!'}


#Re-registration
url = "https://api.whatsapp.com/send?text="+urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")
link = url_shortener_fn(url)
old_reg_sms = key_word+" You are already registered. Support us by asking a friend to volunteer. Click here: "+link
old_reg_sms_dict = {'flow_id':'5ef77ca8d6fc0575c7592c66','message':key_word+" You are already registered. Support us by asking a friend to volunteer. Click here: "+link}
old_reg_whatsapp = "You are already registered as a volunteer with COVIDSOS. We will reach out to you if anyone near your location needs help. This is an *automated* message. Please reach out to wa.me/918618948661 for further queries."
old_reg_whatsapp_img = {'media_link':'cdcdscdc311','caption':'Share this with your friends and family!'}


#New Request
# To requestor
url = "https://covidsos.org/how-it-works"
new_request_link = url_shortener_fn(url)
new_request_sms = key_word+" {name}, we have received your request via {source}. We will call you soon. If urgent, please click "+ new_request_link
new_request_sms_dict = {'flow_id':'','message':key_word+" {name}, we have received your request via {source}. We will call you soon. If urgent, please click "+ link}
new_request_whatsapp = "We have received a help request from you. If you have not filled it, someone would have filled it on your behalf. This is an *automated* message. Please reach out to wa.me/918618948661 for further queries."

# To admin

new_request_mod_sms = key_word+" New query received from {source}. Verify lead by clicking here: "+url_start+"verify/{uuid}"

new_request_mod_sms_dict = {'flow_id':'','message': key_word + " New query received from {source}. Verify lead by clicking here: " + url_start + "verify/{uuid}"}

#Request Verified
# To requestor
url = "https://covidsos.org/how-it-works"
link = url_shortener_fn(url)
request_verified_sms = key_word+" Your request has been verified. We are looking for volunteers. "+str(link)
request_verified_sms_dict = {'flow_id':'','message' : key_word + " Your request has been verified. We are looking for volunteers. " + str(link)}

request_rejected_sms = key_word +" Your request has been cancelled/rejected. If you still need help, please submit request again."
request_rejected_sms = {'flow_id':'','message': key_word + " Your request has been cancelled/rejected. If you still need help, please submit request again."}
# To moderator
request_verified_m_sms1 = key_word + "Request #{r_id} Name: {name} Address: {geoaddress} Mob:{mob_number}. Sent to {v_count_1} nearby & {v_count_2} far volunteers"
request_verified_m_sms2 = "Chat with volunteers using {link}"
request_verified_m_sms1_dict = {'flow_id':'','message':key_word + "Request #{r_id} Name: {name} Address: {geoaddress} Mob:{mob_number}. Sent to {v_count_1} nearby & {v_count_2} far volunteers"}
request_verified_m_sms2_dict = {'flow_id':'','message':"Chat with volunteers using {link}"}


# To volunteer
nearby_v_sms_text = key_word+ " Dear {v_name}, HELP NEEDED in your area. Click {link} to help."
far_v_sms_text = key_word+ " HELP NEEDED in {address}.. Click {link} to help or refer someone."


#Request Accepted
# To volunteer
url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("I have accepted a request and have a query")
link = url_shortener_fn(url)
request_accepted_v_sms = key_word+" Thank you agreeing to help. Name:{r_name} Mob:{mob_number} Request:{request} Address: {address} Click here to speak to us:"+link

# To requestor
url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("My request is accepted and I have a query")
link = url_shortener_fn(url)
request_accepted_r_sms = key_word+" A volunteer has accepted to help you. Click here to speak to us:"+link

# To moderator
request_accepted_m_sms = key_word+" Volunteer {v_name} Mob:{v_mob_number} assigned to {r_name} Mob: {r_mob_number}"

#Request Updated by Volunteer
url = "https://api.whatsapp.com/send?text="+urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")
link = url_shortener_fn(url)

request_closed_v_sms = key_word+" Thank you. This request has been {status} . Every volunteer is a hero. Refer a friend by clicking here "+link
request_closed_m_sms = key_word+" Request {r_id} from {r_name}, {r_mob_number} has been marked as {status} by {v_name},{v_mob_number}. Feedback given is {status_message}"
url = "https://covidsos.org/"
link = url_shortener_fn(url)
request_closed_r_sms = key_word+" Your request has been {status} as per the feedback from volunteer. If you have any further requests, click "+link

# Request updated by admin
url = "https://api.whatsapp.com/send?text="+urllib.parse.quote_plus("Hey, I volunteered for #COVIDSOS. Register as a volunteer and help someone: https://covidsos.org/volunteer :)")
link = url_shortener_fn(url)
a_request_closed_v_sms = key_word+" Thank you. Request assigned to you has been {status} by the {user_name}, COVIDSOS. Every volunteer is a hero. Refer a friend by clicking here "+link
a_request_closed_m_sms = key_word+" Request {r_id} from {r_name}, {r_mob_number}, Volunteer {v_name},{v_mob_number} has been marked as {status} by {user_name}. Feedback given is {status_message}"
url = "https://covidsos.org/"
link = url_shortener_fn(url)
a_request_closed_r_sms = key_word+" Your request has been {status} as per the feedback. If you have any further requests, click "+link



#templates:

whatsapp_temp_1_message = """Hi {v_name}, 
{requestor_name} in your area ({Address}) requires help! *{urgency_status}*


*Why does {requestor_name} need help?*
{reason}


*How can you help {requestor_name}?*
{requirement}

{financial_assistance_status}

Please click here to accept the request: {acceptance_link}

This is a verified request received via www.covidsos.org and it would be great if you can help.!🙂"""










#Bot templates

a = """Dear {v_name}, thank you for messaging COVIDSOS. 

If this is about a request sent to you, kindly click on the link in the message.

If you have any other queries, please click https://covidsos.org/faq

Thank you for your kindness. Support us by asking a friend to volunteer. Click here: http://tinyurl.com/y88n3jpa """


b = """Hi {r_name}, thank you for messaging COVIDSOS.

For queries regarding your existing request, please click https://tinyurl.com/y8fagrwh

To place a new request, please click www.covidsos.org """


# a = """Hi {v_name}, thank you for messaging COVIDSOS.
#
# Please click 1 to know requests assigned to you.
#
# Please click 2 to help someone."""

c = """Hi, thank you for messaging COVIDSOS.

Please click 1 to register as a volunteer.

Please click 2 if you need help."""

c1 ="""Dear user, thank you for willing to step up in times of need. It is easy to now help someone.

Just register on www.covidsos.org as a volunteer.

You will receive a message if anyone near you needs help. """

c2 = """To submit a new request for help, please click here → www.covidsos.org/"""


#
# mod_wait = """Our team will reach out to you shortly"""
# a1 = """Hi {v_name},
# Here are the details of the last accepted request:
# Name: {r_name}
# Address: {adrs}
#
# Why does {r_name} need help?
# {reason}
#
# How can you help {r_name}?
# {requirement}
# This is a verified request received via www.covidsos.org and it would be great if you can help.!🙂
#
# If you have any further concerns regarding this request, please click A."""
#
# a2 = """Dear {v_name},
# Thank you for stepping up in times of need. We will reach out to you if anyone near you needs help. In the meanwhile, here are the list of pending requests www.covidsos.org/pending-requests"""
# b1 = """Dear {r_name}, with regards to your request raised on {date_time}, volunteer {v_name} has agreed to assist you.
#
# He/She shall reach out to you shortly. In case of any issues, kindly click here {link}
#
# If you have any further concerns regarding this request, please click A."""
#
# b2 = """To submit a new request for help, please click here → www.covidsos.org/"""
# c1 ="""Dear user. Thank you for stepping up in times of need. It is easy to now help someone.
#
# Just register on www.covidsos.org as a volunteer.
#
# We will reach out to you if anyone near you needs help. """
#
# c2 = """To submit a new request for help, please click here → www.covidsos.org/"""

inv = """Dear user, kindly enter a valid response.
www.covidsos.org"""

