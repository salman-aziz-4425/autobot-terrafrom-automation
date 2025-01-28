import requests
import json
from datetime import datetime,timedelta
import pandas as pd
from google.oauth2 import service_account
import pandas_gbq as gbq
import pytz
import re
from google.cloud import bigquery
import pymongo
import os
from utils import *
import base64
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def get_locations(api_endpoint, client_id, client_secret, st_app_key, region_name, tenant_id, desired_timezone_name):
  df = pd.DataFrame()
  endpoint_part = api_endpoint.split("/")[-1]
  access_token = get_token(client_id,client_secret)
  headers = {
      'Authorization': f'Bearer {access_token}',
      'ST-App-Key': st_app_key,
  }

  # Define the parameters as a dictionary
  params = {
        "page": '1'
        , "pageSize": '5000'
        ,'includeTotal': 'true'
        ,'modifiedOnOrAfter': str(datetime.now().date() - timedelta(days=121))
  }

  try:
      response = requests.get(api_endpoint, headers=headers,params=params)


      # Check if the request was successful
      if response.status_code == 200:
          # Parse the JSON response
          print(f"Extracted Data from page: {params['page']}")

          df = pd.json_normalize(response.json()['data'], sep='_') #pd.DataFrame(response.json()['data'], columns=[k for k in response.json()['data'][0].keys()])
          df['page'] = response.json()["page"]
          df['pageSize'] = response.json()["pageSize"]
          df['hasMore'] = response.json()["hasMore"]
          df['totalCount'] = response.json()["totalCount"]
          df['tenant'] = tenant_id
          print(response.json()["totalCount"])

      else:
          print("Failed to fetch bookings. Status code:", response.status_code)
          print("Response:", response.text)


      ##########################################
      ########## making concat dataframes#######
      data = pd.DataFrame()
      data = df

      if len(data) > 0:
        total_rows_count = data.totalCount.unique()[0]
        print(f'totallll count ->............. {total_rows_count}')
        if total_rows_count > 5000:
          page_number = 2
          page_count = 5000

          while page_count < total_rows_count:

            access_token = get_token(client_id,client_secret)
            headers = {
                'Authorization': f'Bearer {access_token}',
                'ST-App-Key': st_app_key,
            }
            # Define the parameters as a dictionary
            params = {
                  "page": f'{page_number}'
                  , "pageSize": '5000'
                  ,'includeTotal':'true'
                  ,'modifiedOnOrAfter': str(datetime.now().date() - timedelta(days=121))
            }

            # Make the GET request to fetch bookings
            response = requests.get(api_endpoint, params=params, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                print(f"Extracted Data from page: {params['page']}")
                next_df = pd.json_normalize(response.json()['data'], sep='_') #pd.DataFrame(response.json()['data'], columns=[k for k in response.json()['data'][0].keys()])
                next_df['page'] = response.json()["page"]
                next_df['pageSize'] = response.json()["pageSize"]
                next_df['hasMore'] = response.json()["hasMore"]
                next_df['totalCount'] = response.json()["totalCount"]
                next_df['tenant'] = tenant_id
                data = pd.concat([data, next_df], axis=0, ignore_index=True)

            else:
                print("Failed to fetch. Status code:", response.status_code)
                print("Response:", response.text)

            page_number += 1
            page_count += 5000
        else:
          print('total count is less than 5000')

        data.drop(['customFields', 'tagTypeIds', 'externalData'], axis=1, inplace=True)
        new_df = data.copy()
        columns_to_flatten = {
          'locations': [],
        }

        if len(columns_to_flatten[endpoint_part]) > 0:
          for column in columns_to_flatten[endpoint_part]:
            print(f'Flattening column: {column} .......')
            new_df = flatten_list(new_df, column)

        # Pre-process the date columns and correct the timezone
        dates_to_fix = {
            'locations': ['createdOn', 'modifiedOn'],
        }
        for dt_clm in dates_to_fix[endpoint_part]:
          print(dt_clm)
          new_df[[f'{dt_clm}_date', f'{dt_clm}_time', f'{dt_clm}_timezone']] = new_df[dt_clm].apply(lambda x: utc_to_custom_tz(x, desired_timezone_name))

        new_df['region'] = region_name
        new_df = new_df.astype(str)

        print(len(new_df.columns), len(new_df))
      else:
        print('endpoint has no data')
  except Exception as e:
      print(f"An error occurred: {e}")
  return new_df


def extract_locations(event, context):
  pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
  tenant = pubsub_message['tenant_id']
  project_id = 'autobot-v1-356820'
  dataset_id = f'{tenant}_st_raw_api_scheduler'

  try:
    # Big Query Connection
    organizations = read_big_query_table(dataset_id=dataset_id, table_id='organization_information')
    print(json.dumps({"status":{"code": 200, "text": f"Data successfully loaded from BigQuery."}}))
  except Exception as e:
    print(json.dumps({"status":{"code": 400, "text": f"Error: {e}."}}))
    raise

  tenant_id = tenant
  client_id = organizations[organizations['tenant_id'] == tenant]['organization_client_id'][0]
  client_secret = organizations[organizations['tenant_id'] == tenant]['organization_client_secret'][0]
  st_app_key = organizations[organizations['tenant_id'] == tenant]['organization_app_key'][0]
  timezone_zone = organizations[organizations['tenant_id'] == tenant]['organization_timezone'][0]
  region_name = organizations[organizations['tenant_id'] == tenant]['organization_state'][0]
  api_endpoint = f'https://api.servicetitan.io/crm/v2/tenant/{tenant_id}/locations'

  try:
    location_df = get_locations(api_endpoint, client_id, client_secret, st_app_key, region_name, tenant_id, timezone_zone) 
  except Exception as e:
    print(json.dumps({'status':{'code': 400, 'text': f'Error while extracting data from Service Titan for Tenant Id {tenant_id}: {e}'}}))
    raise
  
  try:
    print(f'----------------------------------- Deleting data from {str(datetime.now().date() - timedelta(days=121))} -----------------------------------')
    delete_big_query_data(credentials_path='cred.json', project_id = project_id, dataset_id = dataset_id, table_id = 'st_get_raw_crm_locations',
    target_column = 'modifiedOn', target_value = str(datetime.now().date() - timedelta(days=121)))
  except Exception as e:
    print(json.dumps({'status':{'code': 400, 'text': f'Error while deleting data from the table: {e}'}}))
    raise

  try:
    print(f'----------------------------------- Loading Data in BigQuery -----------------------------------')
    load_status = bigquery_insert(location_df, tenant_id, project_id=project_id, dataset_id=dataset_id, table_id='st_get_raw_crm_locations', write_disposition='WRITE_APPEND')  
    print(json.dumps({'status': {'code': 200, 'text':'Success'}}))
  except:
    load_status = 'Error while dumping data into Big Query.'
    print(json.dumps({'status':{'code': 400, 'text': f'Error: {load_status}'}}))
    raise