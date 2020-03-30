#!/usr/bin/env python
# coding: utf-8

# In[1]:



import pandas as pd
from connections import connections,keys
import requests


# In[ ]:


def get_ticker_counts():
    server_con = connections('db_read')
    v_q = """Select * from volunteers"""
    v_df = pd.read_sql(v_q,server_con)
    r_q = """Select * from requests"""
    r_df = pd.read_sql(r_q,server_con)
    
    volunteer_count = v_df['mob_number'].nunique()
    request_count = r_df.shape[0]
    pending_request_count = r_df[r_df['status']=='pending'].shape[0]
    return {'volunteer_count':volunteer_count,'request_count':request_count,'pending_request_count':pending_request_count}


# In[ ]:




