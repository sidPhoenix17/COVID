#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Completed
# Google API integration - extract data from spreadsheet
# Map configuration & icons
# Push to website (hosted on BlueHost) automatically
# Secure storage of file without exposure to blog
# Run the script Online in a cron format

#TODO:
# Integrating code with matching algorithm & writing matched entry into spreadsheet


# In[1]:


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

#File Transfer
import ftplib
import os

from connections import connections
from map_generator import public_map,private_map
from settings import *

from database_entry import add_volunteers_to_db
from connections import connections


# In[2]:


# The ID and range of a sample spreadsheet.
volunteer_sheet_data = [{'source':'GreenDream','sheet_id':'1e9H5yO1COGLNfA3lyZxRSgc2llDKRSFZX92Ov8VOzOs','range':'Form Responses 1!A1:K1000','columns': {'Timestamp':'timestamp', 'Full Name':'name', 'WhatsApp Contact Number':'mob_number', 'Email Address':'email_id',
       'Your Location (Prefer mentioning nearest Google Maps Landmark - that you specify on mobile apps like Ola, Uber and Swiggy)':'address',
       'Do you have a grocery and medical store within walking distance of 500 meters?':'grocery_store',
       'GeoStamp':'geostamp', 'GeoAddress':'geoaddress', 'GeoCodeLat':'latitude', 'GeoCodeLon':'longitude'}}]
senior_citizen_sheet_data = [{'source':'GreenDream','sheet_id':'1KrZCG_fYvImIy_-549VB0rzbbfKHkkbmJG0l6DH01zM','range':'Form Responses 1!A1:K1000','columns':{'Timestamp':'timestamp', 'Full Name':'name', 'Mobile Number':'mob_number', 'Age':'age',
       'Your Location (be as precise as possible)':'address',
       'Would you like to give any special instructions to the volunteer aligned to you? Please share below.':'request',
       'Task Status':'status', 'GeoStamp':'geostamp', 'GeoAddress':'geoaddress','GeoCodeLat':'latitude', 'GeoCodeLon':'longitude'}}]

public_file_name= 'output/COVID_SOS_v0.html'
private_file_name= 'output/private_COVID_SOS_v0.html'


# In[3]:


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
        column_rename=i['columns']
        sheets_df_x = sheet_header(extract_sheet(service,sheet_id,range_name),source)
        sheets_df_x = sheets_df_x.rename(columns=column_rename)
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
    input_data = input_data.reset_index(drop=True)
    return input_data


def sheet_clean_up(df,default_r,buffer_radius,user_type='volunteer'):
    # Sample Data
    df = gpd.GeoDataFrame(df)
    print('Received ', df.shape[0], ' responses')
    d = mob_number_clean_up(df[['mob_number']])
    df['mob_number']=d['mob_number']
    df = df[d['mob_number_correct']]
    print('Received ', d[d['mob_number_correct']==False].shape[0], ' responses with incorrect mobile numbers')
    df['latitude']=df['latitude'].astype(float).fillna(0)
    df['longitude']=df['longitude'].astype(float).fillna(0)
    print('Received ', df[(df['latitude']==0)|(df['longitude']==0)].shape[0], ' responses with no location')
    df['radius']=default_r
    geometry = df.apply(lambda x: Point(x['latitude'],x['longitude']).buffer(buffer_radius*x.radius),axis=1)
    crs = {'init': 'epsg:4326'}
    f_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    if(user_type=='volunteer'):
#         f_df['timestamp'] = pd.to_datetime(f_df['timestamp'])
        f_df['icon']='location'
        f_df['country']='India'
    if(user_type=='requests'):
        f_df['icon']='home'
        f_df['country']='India'
        f_df['email_id']=''
    return f_df


def mob_number_clean_up(df):
    #Has space
    df['mob_number']=df['mob_number'].str.replace(" ",'')
    df['mob_number']=df['mob_number'].str.replace(",",'')
    df['mob_number']=df['mob_number'].str.replace("\+91",'')
    df['mob_number']=df['mob_number'].apply(lambda x: str(int(x)))
    #Has zero
    df['mob_number_correct']=df['mob_number'].apply(lambda x: len(str(int(x)))==10)    
    return df


# In[ ]:





# In[4]:


def push_file_to_server(File2Send,Url2Store):
    ftp = connections('ftp')
    Output_Directory = "/public_html/covid19/"
    ftp.cwd(Output_Directory)
    with open(File2Send, "rb") as server_f:
        ftp.storbinary('STOR ' + os.path.basename(Url2Store), server_f)
    print('File saved to server at URL: www.thebangaloreguy.com/covid19/'+(Url2Store).split('/')[-1])
    return None


# In[5]:


def main():
    #Fetching Data from sheets
    print('Running script at',dt.datetime.utcnow()+dt.timedelta(minutes=330))
    service = google_api_activation()
    print('Google Authentication completed')
    volunteer_df = extract_all_sheets(service,volunteer_sheet_data)
    volunteer_df['TYPE']='VOLUNTEER'
    requests_df = extract_all_sheets(service,senior_citizen_sheet_data)
    requests_df['TYPE']='REQUEST'
    
    v_df = sheet_clean_up(volunteer_df,default_r,buffer_radius,'volunteer')
    v_db_status, response = add_volunteers_to_db(v_df)
    print('DB Update Status: ', v_db_status)
    print('Message:', response)
    r_df = sheet_clean_up(requests_df,default_r,buffer_radius,'requests')
    #add_requests(r_df.rename(columns={'email_d':'email_id'})[['timestamp', 'name', 'mob_number', 'email_id', 'country', 'address', 'geoaddress', 'latitude', 'longitude', 'source', 'request', 'age']])
    private_map_v1 = private_map(v_df,r_df,private_file_name,map_pkg='kepler')
    push_file_to_server(private_file_name,private_file_name)
    push_file_to_server(private_file_name,'output/share_and_survive_v0_dark.html')
    public_map_v1 = public_map(v_df,r_df,public_file_name,map_pkg='kepler')
    push_file_to_server(public_file_name,public_file_name)
    #Processing Data
    return v_df, r_df, private_map_v1,public_map_v1


# In[6]:


v_df, r_df, p1,p2=main()


# In[ ]:


#v_df[['Lat','Lon','Full Name','TYPE']].rename(columns={'Full Name':'name','Lat':'lat','Lon':'lon','TYPE':'type'}).to_json(orient='table',index=False)

#r_df[['Lat','Lon','Full Name','TYPE']].rename(columns={'Full Name':'name','Lat':'lat','Lon':'lon','TYPE':'type'}).to_json(orient='table',index=False)


# In[ ]:


# with open('map_config/map_config_public.py','w') as f:
#     f.write('public_live_config = {}'.format(map_1.config))
# with open('map_config/map_config_new.py','r') as f:
#     print(f.read())


# In[ ]:


#v_query = ("""Select * from volunteers""")
#v_data = pd.read_sql(v_query,server_con)

#v_df.to_sql(name = 'volunteers', con = engine, schema='thebang7_COVID_SOS', if_exists='append', index = False,index_label=None)


# In[ ]:



#Delete command
#ftp.delete(os.path.basename(File2Send))


# In[ ]:


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

