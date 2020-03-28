#!/usr/bin/env python
# coding: utf-8

# In[1]:



#DB Connections
import mysql.connector as sql_con
from sqlalchemy import create_engine
import cred_config as cc
import ftplib


# In[2]:


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

def keys(api_name):
    if(api_name=='gmap'):
        gmap_key = cc.credentials['gmap']['key']
    return gmap_key


# In[ ]:




