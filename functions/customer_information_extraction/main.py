import requests
import pandas as pd
import json
from datetime import datetime,timedelta
import pandas as pd
from google.oauth2 import service_account
import pandas_gbq as gbq
import pandas as pd
import pytz
from datetime import datetime
import re
from google.cloud import bigquery
import os
from utils import bigquery_insert
import base64


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def transform(event, context):
  pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
  tenant = pubsub_message['tenant_id']
  project_id = 'autobot-v1-356820'
  dataset_id = f'{tenant}_st_raw_api_scheduler'

  # Replace 'your-service-account-key.json' with the path to your service account key file
  credentials = service_account.Credentials.from_service_account_file(
      'cred.json',
      scopes=['https://www.googleapis.com/auth/bigquery']
  )

  # Set your specific date
  specific_date = str(datetime.now().date())

  # Construct your query with a WHERE clause to filter by date
  query = f"""
      SELECT *
      FROM `{project_id}.{dataset_id}.st_get_raw_crm_customers`
      WHERE modifiedOn_date = '{specific_date}'
  """

  # Use the Google Cloud client library to execute the query
  client = bigquery.Client(credentials=credentials)
  customers_df = client.query(query).to_dataframe()
  customers_df.rename(columns={"id": "customer_id", 'type': 'customer_type', 'name': 'customer_name', 'active': 'customer_is_active'}, inplace=True)
  customers_df = customers_df[['customer_id', 'modifiedOn_date', 'customer_is_active', 'customer_name', 'customer_type', 'doNotMail', 'doNotService',
      'address_street', 'address_unit', 'address_city', 'address_state', 'address_zip', 'address_country', 'address_latitude',
      'address_longitude', 'tenant']]
  print(len(customers_df))
  
  job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ArrayQueryParameter("ids", "STRING", customers_df['customer_id'].tolist()),
    ]
  )

  if len(customers_df) > 0:

    cc_query = f"""
      SELECT *
      FROM `{project_id}.{dataset_id}.st_get_raw_crm_customers_contacts`
      WHERE customerId IN UNNEST(@ids)
    """

    customer_contact_df = client.query(cc_query, job_config=job_config).to_dataframe()
    customer_contact_df.rename(columns={"customerId": "customer_id", "id": "contact_id"}, inplace=True)
    customer_contact_df = customer_contact_df[['customer_id', 'contact_id', 'type', 'value', 'phoneSettings_phoneNumber', 'phoneSettings_doNotText', 'phoneSettings',
          'tenant', 'modifiedOn_timezone']]
    print(len(customer_contact_df))

    lo_query = f"""
      SELECT *
      FROM `{project_id}.{dataset_id}.st_get_raw_crm_locations`
      WHERE customerId IN UNNEST(@ids)
    """

    locations_df = client.query(lo_query, job_config=job_config).to_dataframe()
    locations_df.rename(columns={"id": "location_id", "customerId": "customer_id", "name": "customer_name", "address_street":"location_street", "address_unit":"location_unit", "address_city":"location_city", "address_state":"location_state", "address_zip": "location_zip", "address_country":"location_country"}, inplace=True)
    print(len(locations_df))

    mem_query = f"""
      SELECT customerId, status, active,`to`, modifiedOn,tenant
      FROM `{project_id}.{dataset_id}.st_get_raw_membership_memberships`
    """

    members_df = client.query(mem_query).to_dataframe()

    # drop duplicate members_df['customerId']
    members_df = members_df.sort_values(by=['to','modifiedOn'], ascending=[False, False])
    members_df = members_df.drop_duplicates(subset=['customerId'])

    # members_df.rename(columns= {"customerId": "customer_id", "status": "membership_status", "active": "is_member"}, inplace=True)
    members_df.rename(columns= {"customerId": "customer_id", "status": "membership_status"}, inplace=True)
    print(len(members_df))

    for index, row in members_df.iterrows():
        if row['membership_status'] == 'Active':
            members_df.loc[index, 'is_member'] = True  # Update 'is_member' for the current row
        else:
            members_df.loc[index, 'is_member'] = False

    # Merge and perform the operations using pandas
    result_df = pd.merge(left=customers_df, right=customer_contact_df, on=['customer_id', 'tenant'], how='left')
    # Merge
    final_df = pd.merge(left=result_df, right=locations_df[['location_id', 'location_street', 'location_unit', 'location_city', 'location_state', 'location_zip', 'location_country', 'customer_id', 'tenant']], on=['customer_id', 'tenant'], how='inner')
    # Merge
    last_df = pd.merge(left=final_df, right=members_df[['membership_status', 'is_member', 'customer_id', 'tenant']], on=['customer_id', 'tenant'], how='left')
    last_df['is_member'] = last_df['is_member'].fillna(False)
    last_df['membership_status'] = last_df['membership_status'].fillna('Inactive')
    # remove duplicate
    last_df = last_df.drop_duplicates(subset=['customer_id','value','location_id'])
    
    try:
      # Construct the DELETE statement
      delete_query = f"""
          DELETE FROM `{project_id}.{dataset_id}.customer_information`
          WHERE customer_id IN UNNEST(@ids)
      """
      query_job = client.query(delete_query, job_config=job_config)

      # Wait for the query to finish executing
      query_job.result()
      print(f"Data Deleted Successfully for ids {', '.join(customers_df['customer_id'].tolist())}")

    except Exception as e:
      print(f"Issue in deleting data for ids {', '.join(customers_df['customer_id'].tolist())}: {e}")
      raise

    try:
        load_status = bigquery_insert(last_df, None, project_id=project_id, dataset_id=dataset_id, table_id='customer_information', write_disposition='WRITE_APPEND')
        print(load_status)
    except Exception as e:
      print(f"Error Loading data in Big Query: {e}.")
      raise

  else:
    print('No Modifications in the data.')

