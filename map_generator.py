#!/usr/bin/env python
# coding: utf-8

# In[3]:


#Kepler
#Folium
#Mapbox


# In[4]:


import numpy as np
import pandas as pd
import geopandas as gpd

#Map
import keplergl

from bs4 import BeautifulSoup
#FORMAT: from map_config.filename import *
from map_config.map_config_private import *
from map_config.map_config_public import *


# In[ ]:


def html_file_changes(output_file_name):
    with open(output_file_name,'r') as file:
        filedata = file.read()
        filedata = filedata.replace('keplergl-jupyter-html','covid-sos-page')
        filedata = filedata.replace('UA-64694404-19','UA-143016880-1')
    with open(output_file_name,'w') as file:
        file.write(filedata)
    with open(output_file_name,'r') as output_file_reader:
        bs = output_file_reader.read()
    soup = BeautifulSoup(bs, 'html.parser')
    soup.title.string='COVID SOS Initiative - Connecting Volunteers with Requests'
    #Enabling GA
    with open(output_file_name, "w") as file:
        file.write(str(soup))
    return None


# In[ ]:


def public_map(v_df,r_df,output_file_name,map_pkg='kepler'):
    if(map_pkg=='kepler'):
        v_df['WhatsApp Contact Number']=9582148040
        r_df['Mobile Number']=9582148040
        map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df.loc[v_df['Lat']!=0,['Timestamp', 'Full Name','geometry','Lat','Lon','radius','icon','TYPE']],
                                                   'requests_data':r_df.loc[r_df['Lat']!=0,['Timestamp', 'Full Name', 'Mobile Number', 'Age'
        ,'Would you like to give any special instructions to the volunteer aligned to you? Please share below.','Task Status','geometry','Lat','Lon','radius','icon','TYPE']]})
        print('The public map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
        #variable live_config is defined when "file" is executed
        if(public_live_config):
            map_1.config = public_live_config
        map_1.save_to_html(file_name=output_file_name)
        html_file_changes(output_file_name)
    return map_1

def private_map(v_df,r_df,output_file_name,map_pkg='kepler'):
    if(map_pkg=='kepler'):
        r_df = r_df[r_df['Task Status']=='Pending']
        map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df[v_df['Lat']!=0],'requests_data':r_df[r_df['Lat']!=0]})
        print('The private Map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
        #variable live_config is defined when "file" is executed
        if(private_live_config):
            map_1.config = private_live_config
        map_1.save_to_html(file_name=output_file_name)
        html_file_changes(output_file_name)
    return map_1


# In[ ]:


def map_config_fn(map_config_file):
    with open(map_config_file,'r') as config_file_reader:
        config_file = config_file_reader.read()
        exec(config_file, None, locals())
    dx = live_config.copy()
    return dx

