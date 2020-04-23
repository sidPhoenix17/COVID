
import urllib
import requests

def url_shortener_fn(input_url):
    url = 'http://tinyurl.com/api-create.php'
    params = {'url':input_url}
    request = requests.get(url=url,params=params)
    if(request.text=='Error'):
        return input_url
    else:
        return request.text

    
#New User 
url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("I have registered!")
link = url_shortener_fn(url)
new_reg_sms = "[COVIDSOS] Thank you for registering. Click here to contact us:"+link
new_reg_whatsapp = "Thank you for registering as a volunteer with COVIDSOS. We will reach out to you if anyone near your location needs help. This is an *automated* message. Please reach out to wa.me/918618948661 for further queries."
new_reg_whatsapp_img = {'media_link':'cdcdscdc311','caption':'Share this with your friends and family!'}


#Re-registration
url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus("I have registered!")
link = url_shortener_fn(url)
old_reg_sms = "[COVIDSOS] You are already registered with us. Click here to contact us:"+link
old_reg_whatsapp = "You are already registered as a volunteer with COVIDSOS. We will reach out to you if anyone near your location needs help. This is an *automated* message. Please reach out to wa.me/918618948661 for further queries."
old_reg_whatsapp_img = {'media_link':'cdcdscdc311','caption':'Share this with your friends and family!'}


#New Request - to requestor
url = "https://wa.me/918618948661?text="+urllib.parse.quote_plus('Hi')
link = url_shortener_fn(url)
new_request_sms = "[COVIDSOS] "+name+", we have received your request. We will call you soon. If urgent, please click "+url
new_request_whatsapp = "We have received a help request from you. If you have not filled it, someone would have filled it on your behalf. This is an *automated* message. Please reach out to wa.me/918618948661 for further queries."

#New Request - to admin



#Request Verified - to requestor


#Request Verified - to admin


#Request Verified - to user


