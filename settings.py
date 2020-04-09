import os
from local_settings import server_type,SECRET_KEY,sms_key,sms_sid
import numpy as np
default_r=0.5

#Approximation
lat_deg_to_km = 95.0
lon_deg_to_km = 110.0
buffer_radius = 1/np.sqrt(95*95+110*110)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# SECRET_KEY = os.getenv('SECRET_KEY')
sms_url = "https://api.msg91.com/api/v2/sendsms"
EARTH_RADIUS = 6378000
neighbourhood_radius = 1
moderator_list=[9582148040,9910857735,8618948661]
search_radius=15

mail_config = {
    'MAIL_SERVER': 'smtp.googlemail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': 'covidsos60@gmail.com',
    'MAIL_DEFAULT_SENDER': 'covidsos60@gmail.com',
    'MAIL_PASSWORD': 'cov!dSos@60'
}