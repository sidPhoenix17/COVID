#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Completed
# Google API integration - extract data from spreadsheet
# Map configuration & icons
# Push to website (hosted on BlueHost) automatically
# Secure storage of file without exposure to blog

#TODO:
# Run the script Online in a cron format
# Integrating code with matching algorithm & writing matched entry into spreadsheet


# In[2]:


#Basic
from __future__ import print_function
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

#Google Docs integration
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

#Map
import keplergl

#DB Connections
import mysql.connector as sql_con
from sqlalchemy import create_engine
import cred_config as cc

#File Transfer
import ftplib
import os

from bs4 import BeautifulSoup


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

output_file_name= 'output/COVID_SOS_v0.html'

# map_config='map_config/live_config_dark.py'
map_config='map_config/live_config_light.py'
with open(map_config,'r') as f:
    file = f.read()
    exec(str(file))

mask_numbers = True


# In[4]:


def connections(con_name):
    if(con_name=='db_read'):
        cred_r=cc.credentials['covid_sos_read']
        server_con = sql_con.connect(user=cred_r['user'], password=cred_r['password'], host=cred_r['host'],database=cred_r['database'])
    if(con_name=='db_write'):
        cred_w = cc.credentials['covid_sos_write']
        server_con = create_engine("mysql+pymysql://{user}:{password}@{host}/{database}".format(user = cred_w['user'], password = cred_w['password'], host = cred_w['host'], database = cred_w['database']), pool_size=10, max_overflow=20, echo=False)
    if(con_name=='ftp'):
        FTP_con = cc.credentials['ftp']
        server_con = ftplib.FTP(host=FTP_con['host'], user=FTP_con['user'], passwd=FTP_con['password'])
    return server_con


# In[5]:


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


def html_file_changes(output_file_name):
    with open(output_file_name,'r') as f:
        bs = f.read()
    soup = BeautifulSoup(bs, 'html.parser')
    soup.title.string='COVID SOS Initiative - Connecting Volunteers with Requests'
    with open(output_file_name, "w") as file:
        file.write(str(soup))
    return None


# In[6]:



def push_file_to_server(File2Send):   
    ftp = connections('ftp')
    Output_Directory = "/public_html/covid19/"
    ftp.cwd(Output_Directory)
    with open(File2Send, "rb") as f:
        ftp.storbinary('STOR ' + os.path.basename(File2Send), f) 
    print('File saved to server')
    return None


# In[7]:


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
    if(mask_numbers):
        v_df['WhatsApp Contact Number']=9582148040
        r_df['Mobile Number']=9582148040
    map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df[v_df['Lat']!=0],'requests_data':r_df[r_df['Lat']!=0]})
    print('The Map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
    #variable live_config is defined when "file" is executed
    map_1.config = live_config
    map_1.save_to_html(file_name=output_file_name)
    html_file_changes(output_file_name)
    push_file_to_server(output_file_name)
    #Processing Data
    return v_df, r_df, map_1


# In[8]:


v_df, r_df, map_1=main()


# In[9]:


#v_query = ("""Select * from volunteers""")
#v_data = pd.read_sql(v_query,server_con)

#v_df.to_sql(name = 'volunteers', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)


# In[10]:



#Delete command
#ftp.delete(os.path.basename(File2Send))


# In[ ]:





# In[ ]:




