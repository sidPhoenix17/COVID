#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Completed
# Google API integration - extract data from spreadsheet
# Map configuration & icons

#TODO:
# Push to website (hosted on BlueHost) automatically
# Run the script Online in a cron format
# Secure storage of file without exposure to blog
# Integrating code with matching algorithm & writing matched entry into spreadsheet


# In[2]:


from __future__ import print_function
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import keplergl


# In[3]:



default_r=0.5

#Approximation
lat_deg_to_km = 95.0
lon_deg_to_km = 110.0
buffer_radius = 1/np.sqrt(95*95+110*110)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
Volunteer_Sheet_ID = '1e9H5yO1COGLNfA3lyZxRSgc2llDKRSFZX92Ov8VOzOs'
Senior_citizen_sheet_ID = '1KrZCG_fYvImIy_-549VB0rzbbfKHkkbmJG0l6DH01zM'
Range_name = 'Form Responses 1!A1:K1000'

# map_config='map_config/live_config_dark.py'
map_config='map_config/live_config_light.py'
with open(map_config,'r') as f:
    file = f.read()
    exec(str(file))


# In[4]:


def google_api_activation():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('support_files/token.pickle'):
        with open('support_files/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('support_files/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('support_files/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    return service


def extract_sheet(service,sheet_id,range_name):
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id,range=range_name).execute()
    return result

def sheet_header(df):
    input_data = pd.DataFrame(df['values'])
    new_header = input_data.iloc[0] #grab the first row for the header
    input_data = input_data[1:] #take the data less the header row
    input_data.columns = new_header #
    return input_data


def sheet_clean_up(df,default_r,buffer_radius):
    
    # Sample Data
    df = gpd.GeoDataFrame(df)
    df['Lat']=df['GeoCodeLat'].astype(float).fillna(0)
    df['Lon']=df['GeoCodeLon'].astype(float).fillna(0)
    df['radius']=default_r
    geometry = df.apply(lambda x: Point(x['Lon'],x['Lat']).buffer(buffer_radius*x.radius),axis=1)
    crs = {'init': 'epsg:4326'}
    f_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry).drop(columns=['GeoCodeLat','GeoCodeLon'])
    return f_df


# In[5]:


def main():
    #Fetching Data from sheets
    service = google_api_activation()
    volunteer_df = sheet_header(extract_sheet(service,Volunteer_Sheet_ID,Range_name))
    requests_df = sheet_header(extract_sheet(service,Senior_citizen_sheet_ID,Range_name))
    v_df = sheet_clean_up(volunteer_df,default_r,buffer_radius)
    v_df['icon']='location'
    r_df = sheet_clean_up(requests_df,default_r,buffer_radius)
    r_df = r_df[r_df['Task Status']=='Pending']
    r_df['icon']='home'
    map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df[v_df['Lat']!=0],'requests_data':r_df[r_df['Lat']!=0]})
    print('The Map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
    #variable live_config is defined when "file" is executed
    map_1.config = live_config
    map_1.save_to_html(file_name='output/share_and_survive_v0.html')
    #Processing Data
    return v_df, r_df, map_1


# In[6]:


v_df, r_df, map_1=main()


# In[ ]:




