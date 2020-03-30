#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from flask import Flask,request
import pandas as pd
from connections import connections
import datetime as dt

from database_entry import add_requests

from settings import *


# In[ ]:


app = Flask(__name__)


# In[ ]:


# 1. request help
#To Do
# 2. volunteer register
# 3. org register
# 4. login
# 5. user register (by you)
# 6. get map data - open
# 7. get map data - authorised, all details
# 8. assign user


# In[ ]:


@app.route('/create_volunteer',methods=['POST'])
def create_request():
    name = request.args['name']
    mob_number = request.args['mob_number']
    age = request.args['age']
    address = request.args['address']
    user_request = request.args['request']
    latitude = request.args['latitude']
    longitude = request.args['longitude']
    current_time = dt.datetime.utcnow()+dt.timedelta(minutes=330)
    req_dict = {'timestamp':[current_time],'name':[name],'mob_number':[mob_number],'email_id':[''],
                'country':['India'],'address':[address],'geoaddress':[address],'latitude':[latitude], 'longitude':[longitude],
                'source':['website'],'age':[age],'request':[user_request]}
    df = pd.DataFrame(req_dict)
    expected_columns=['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']
    x,y = add_requests(df)
    print(x)
    print(y)
    return None


# In[ ]:


if(server=='local'):
    if __name__ == '__main__':    
        app.run(debug=True,use_reloader=False)

if(server=='server'):
    if __name__ =='__main__':
        app.run()


# In[ ]:




