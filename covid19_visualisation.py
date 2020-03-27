#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Completed
# Google API integration - extract data from spreadsheet
# Map configuration & icons
# Push to website (hosted on BlueHost) automatically
# Secure storage of file without exposure to blog
# Run the script Online in a cron format

#TODO:
# Integrating code with matching algorithm & writing matched entry into spreadsheet


# In[2]:


#Basic
from __future__ import print_function
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import datetime as dt

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
volunteer_sheet_data = [{'source':'GreenDream','sheet_id':'1e9H5yO1COGLNfA3lyZxRSgc2llDKRSFZX92Ov8VOzOs','range':'Form Responses 1!A1:K1000'}]
senior_citizen_sheet_data = [{'source':'GreenDream','sheet_id':'1KrZCG_fYvImIy_-549VB0rzbbfKHkkbmJG0l6DH01zM','range':'Form Responses 1!A1:K1000'}]

public_file_name= 'output/COVID_SOS_v0.html'
private_file_name= 'output/private_COVID_SOS_v0.html'

#FORMAT: from map_config.filename import *
from map_config.map_config_private import *
from map_config.map_config_public import *


# In[4]:


def map_config_fn(map_config_file):
    with open(map_config_file,'r') as config_file_reader:
        config_file = config_file_reader.read()
        exec(config_file, None, locals())
    dx = live_config.copy()
    return dx


# In[5]:


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


# In[6]:


def google_api_activation():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('support_files/token.pickle'):
        with open('support_files/token.pickle', 'rb') as token1:
            creds = pickle.load(token1)
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

def extract_all_sheets(service,sheets_dict):
    sheets_df=pd.DataFrame()
    for i in sheets_dict:
        source = i['source']
        sheet_id=i['sheet_id']
        range_name=i['range']
        sheets_df_x = sheet_header(extract_sheet(service,sheet_id,range_name),source)
        sheets_df = sheets_df.append(sheets_df_x)
    return sheets_df

def extract_sheet(service,sheet_id,range_name):
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id,range=range_name).execute()
    return result

def sheet_header(df,source):
    input_data = pd.DataFrame(df['values'])
    new_header = input_data.iloc[0] #grab the first row for the header
    input_data = input_data[1:] #take the data less the header row
    input_data.columns = new_header #
    input_data['source']=source
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
    with open(output_file_name,'r') as output_file_reader:
        bs = output_file_reader.read()
    soup = BeautifulSoup(bs, 'html.parser')
    soup.title.string='COVID SOS Initiative - Connecting Volunteers with Requests'
    with open(output_file_name, "w") as file:
        file.write(str(soup))
    return None


# In[7]:


def public_map(v_df,r_df,output_file_name):
    v_df['WhatsApp Contact Number']=9582148040
    r_df['Mobile Number']=9582148040
    map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df.loc[v_df['Lat']!=0,['Timestamp', 'Full Name','geometry','Lat','Lon','radius','icon']],
                                               'requests_data':r_df.loc[r_df['Lat']!=0,['Timestamp', 'Full Name', 'Mobile Number', 'Age'
    ,'Would you like to give any special instructions to the volunteer aligned to you? Please share below.','Task Status','geometry','Lat','Lon','radius','icon']]})
    print('The public map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
    #variable live_config is defined when "file" is executed
    map_1.config = public_live_config
    map_1.save_to_html(file_name=output_file_name)
    html_file_changes(output_file_name)
    push_file_to_server(output_file_name,output_file_name)
    push_file_to_server(output_file_name,'output/share_and_survive_v0_dark.html')
    return map_1

def private_map(v_df,r_df,output_file_name):
    r_df = r_df[r_df['Task Status']=='Pending']
    map_1 = keplergl.KeplerGl(height=800,data={'volunteer_data':v_df[v_df['Lat']!=0],'requests_data':r_df[r_df['Lat']!=0]})
    print('The private Map contains ', v_df[v_df['Lat']!=0].shape[0],' volunteers and ', r_df[r_df['Lat']!=0].shape[0], ' pending requests')
    #variable live_config is defined when "file" is executed
    map_1.config = private_live_config
    map_1.save_to_html(file_name=output_file_name)
    html_file_changes(output_file_name)
    push_file_to_server(output_file_name,output_file_name)
    return map_1


def push_file_to_server(File2Send,Url2Store):
    ftp = connections('ftp')
    Output_Directory = "/public_html/covid19/"
    ftp.cwd(Output_Directory)
    with open(File2Send, "rb") as server_f:
        ftp.storbinary('STOR ' + os.path.basename(Url2Store), server_f) 
    print('File saved to server at URL: www.thebangaloreguy.com/covid19/'+(Url2Store).split('/')[-1])
    return None


# In[8]:


def main():
    #Fetching Data from sheets
    print('Running script at',dt.datetime.utcnow()+dt.timedelta(minutes=330))
    service = google_api_activation()
    volunteer_df = extract_all_sheets(service,volunteer_sheet_data)
    requests_df = extract_all_sheets(service,senior_citizen_sheet_data)
    
    v_df = sheet_clean_up(volunteer_df,default_r,buffer_radius)
    v_df['icon']='location'
    
    r_df = sheet_clean_up(requests_df,default_r,buffer_radius)
    r_df['icon']='home'
    
    private_map_v1 = private_map(v_df,r_df,private_file_name)
    public_map_v1 = public_map(v_df,r_df,public_file_name)
    #Processing Data
    return v_df, r_df, private_map_v1,public_map_v1


# In[9]:


v_df, r_df, p1,p2=main()


# In[10]:


# with open('map_config/map_config_public.py','w') as f:
#     f.write('public_live_config = {}'.format(map_1.config))
# with open('map_config/map_config_new.py','r') as f:
#     print(f.read())


# In[11]:


#v_query = ("""Select * from volunteers""")
#v_data = pd.read_sql(v_query,server_con)

#v_df.to_sql(name = 'volunteers', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)


# In[12]:



#Delete command
#ftp.delete(os.path.basename(File2Send))


# In[ ]:





# In[13]:


# from folium import Map, Marker, GeoJson
# from folium.plugins import MarkerCluster


# v_df

# #quick visualization on map of raw data

# m = Map(location= [12.97194, 77.59369], zoom_start= 12, tiles="cartodbpositron", 
#         attr= '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="http://cartodb.com/attributions#basemaps">CartoDB</a>' 
# )
# mc = MarkerCluster()

# for i in v_df.index:
#     mk = Marker(location=[v_df.loc[i,'Lat'],v_df.loc[i,'Lon']])
#     mk.add_to(mc)
# mc.add_to(m)

# m.save('folium_view.html')
# m

