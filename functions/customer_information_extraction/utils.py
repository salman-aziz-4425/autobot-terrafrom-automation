import requests
import pymongo
import pandas as pd
import pandas_gbq as gbq
import pytz
import re
import os
from google.cloud import bigquery
from dateutil import parser
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime


def create_bigquery_dataset(project_id, dataset_id):
    """
    Create a BigQuery dataset.

    Args:
        project_id (str): The ID of the Google Cloud project.
        dataset_id (str): The ID of the dataset to be created.
    """
    try:
        # Initialize the BigQuery client
        client = bigquery.Client.from_service_account_json('./cred.json')
        # Construct a reference to the dataset
        dataset_ref = client.dataset(dataset_id)
        # Create the dataset object
        dataset = bigquery.Dataset(dataset_ref)
        # Send the dataset creation request
        dataset = client.create_dataset(dataset)
        print(f"Dataset {dataset.dataset_id} created.")
    except Exception as e:
        print(f"Error creating dataset: {e}")


def connect_mongo(mongo_uri: str, database: str, collection: str):
    """
    Connect to MongoDB and return the specified collection.
    
    Args:
        mongo_uri (str): The MongoDB connection URI.
        database (str): The name of the database.
        collection (str): The name of the collection.

    Returns:
        pymongo.collection.Collection: The specified collection.
    """
    myclient = pymongo.MongoClient(mongo_uri)
    mydb = myclient[database]
    mycol = mydb[collection]
    return mycol


def exec_mongo_query(collection, key: str, value: str):
    """
    Execute a MongoDB query to find a document with the specified key-value pair.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to query.
        key (str): The key to search for in the document.
        value (str): The value corresponding to the key.

    Returns:
        dict: The document matching the query, or None if not found.
    """
    query = {key: value}
    result = collection.find_one(query)
    return result


def flatten_list(df, col_name):
  # Replace empty lists with None (null values)
  # df[col_name] = df[col_name].apply(lambda x: x if len(x) > 0 else None)

  # Use the explode function to generate rows based on the list values
  df = df.explode(col_name, ignore_index=True)

  if col_name == 'items':
        # Use pandas.json_normalize to expand the dictionaries into columns
        df_normalized = pd.json_normalize(df['items'], sep="_")
        df_normalized.columns = [f"items_{clm}" for clm in df_normalized.columns]
        # Combine the original DataFrame with the normalized DataFrame
        df_result = pd.concat([df.drop('items', axis=1), df_normalized], axis=1)
        df = df_result
        df.reset_index(drop=True, inplace=True)
  elif col_name == 'customFields':
        # Use pandas.json_normalize to expand the dictionaries into columns
        df_normalized = pd.json_normalize(df['customFields'], sep="_")
        df_normalized.columns = [f"customFields_{clm}" for clm in df_normalized.columns]
        # Combine the original DataFrame with the normalized DataFrame
        df_result = pd.concat([df.drop('customFields', axis=1), df_normalized], axis=1)
        df = df_result
        df.reset_index(drop=True, inplace=True)
  elif col_name == 'appliedTo':
        # Use pandas.json_normalize to expand the dictionaries into columns
        df_normalized = pd.json_normalize(df['appliedTo'], sep="_")
        df_normalized.columns = [f"appliedTo_{clm}" for clm in df_normalized.columns]
        # Combine the original DataFrame with the normalized DataFrame
        df_result = pd.concat([df.drop('appliedTo', axis=1), df_normalized], axis=1)
        df = df_result
        df.reset_index(drop=True, inplace=True)
  elif col_name == 'rates':
        # Use pandas.json_normalize to expand the dictionaries into columns
        df_normalized = pd.json_normalize(df['rates'], sep="_")
        df_normalized.columns = [f"rates_{clm}" for clm in df_normalized.columns]
        # Combine the original DataFrame with the normalized DataFrame
        df_result = pd.concat([df.drop('rates', axis=1), df_normalized], axis=1)
        df = df_result
        df.reset_index(drop=True, inplace=True)
  elif col_name == 'splits':
        # Use pandas.json_normalize to expand the dictionaries into columns
        df_normalized = pd.json_normalize(df['splits'], sep="_")
        df_normalized.columns = [f"splits_{clm}" for clm in df_normalized.columns]
        # Combine the original DataFrame with the normalized DataFrame
        df_result = pd.concat([df.drop('splits', axis=1), df_normalized], axis=1)
        df = df_result
        df.reset_index(drop=True, inplace=True)
  else:
    print('col doesnt exsist')
    df.reset_index(drop=True, inplace=True)

  return df


def get_token(client_id, client_secret):
    """
    Obtains an access token from a ServiceTitan authentication server using client credentials.

    Parameters:
    - client_id (str): The client ID used for authentication.
    - client_secret (str): The client secret used for authentication.

    Returns:
    - str: The access token retrieved from the authentication server.
    """
    url = "https://auth.servicetitan.io/connect/token"

    # Prepare payload for client credentials grant type
    payload = f'grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}'

    # Set headers for the request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make a POST request to obtain the access token
    response = requests.post(url, headers=headers, data=payload)

    # Retrieve and return the access token from the response JSON
    access_token = response.json()['access_token']
    return access_token


def bigquery_insert(df, tenant_id, project_id='autobot-v1-356820', dataset_id='temporary_db_247360145', table_id='upcoming_appointment_and_capacity', write_disposition='WRITE_TRUNCATE'):
    """
    Inserts a DataFrame into a specified BigQuery table.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be inserted.
    - tenant_id (str): The tenant ID associated with the data.
    - project_id (str): Google Cloud project ID (default: 'autobot-v1-356820').
    - dataset_id (str): BigQuery dataset ID (default: 'temporary_db_247360145').
    - table_id (str): BigQuery table ID (default: 'upcoming_appointment_and_capacity').
    - write_disposition (str): Write disposition option (default: 'WRITE_TRUNCATE').
        Options: 'WRITE_TRUNCATE' (replace existing data), 'WRITE_APPEND' (append to existing data), 'WRITE_EMPTY' (fail if table is not empty).

    Returns:
    - str: Status message indicating success or an error message.
    """
    try:
        # Set the path to your BigQuery credentials JSON file
        credentials_path = 'cred.json'

        # Set the environment variable for Google Cloud credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        if 'is_member' in df.columns:
            df['is_member'] = df['is_member'].astype(pd.BooleanDtype()) 
        # Create a BigQuery client
        client = bigquery.Client()

        # Convert DataFrame to BigQuery table
        table_ref = client.dataset(dataset_id).table(table_id)
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,  # Options: WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY
        )

        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete

        return 'Inserted'
    except Exception as e:
        return f'Insertion Error: {e}'
    
        
def encrypt(input_string, n=2):
    """
    Encrypts a given input string using a Caesar cipher.

    Parameters:
    - input_string (str): The string to be encrypted.
    - n (int): The number of positions to shift each character in the alphabet (default: 2).

    Returns:
    - str: The encrypted string.
    """
    encrypted_string = ""
    for char in input_string:
        if char.isalpha():
            is_upper = char.isupper()
            base_code = ord('A') if is_upper else ord('a')
            shifted_code = (ord(char) - base_code + n) % 26 + base_code
            encrypted_string += chr(shifted_code)
        elif char.isdigit():
            # Shift digits by n
            shifted_digit = (int(char) + n) % 10
            encrypted_string += str(shifted_digit)
        else:
            encrypted_string += char
    return encrypted_string


def decrypt(input_string, n=2):
    """
    Decrypts a given input string that was encrypted using a Caesar cipher.

    Parameters:
    - input_string (str): The string to be decrypted.
    - n (int): The number of positions by which each character was shifted in the original encryption (default: 2).

    Returns:
    - str: The decrypted string.
    """
    decrypted_string = ""
    for char in input_string:
        if char.isalpha():
            is_upper = char.isupper()
            base_code = ord('A') if is_upper else ord('a')
            shifted_code = (ord(char) - base_code - n + 26) % 26 + base_code
            decrypted_string += chr(shifted_code)
        elif char.isdigit():
            # Shift digits back by n
            shifted_digit = (int(char) - n + 10) % 10
            decrypted_string += str(shifted_digit)
        else:
            decrypted_string += char
    return decrypted_string


def read_big_query_table(credentials_path='cred.json', project_id='autobot-v1-356820', dataset_id='test_247360145_247360145', table_id='customer_information_test'):
    """
    Reads data from a BigQuery table and returns it as a pandas DataFrame.

    Parameters:
    - credentials_path (str): Path to the Google Cloud credentials JSON file (default: 'cred.json').
    - project_id (str): Google Cloud project ID (default: 'autobot-v1-356820').
    - dataset_id (str): BigQuery dataset ID (default: 'test_247360145_247360145').
    - table_id (str): BigQuery table ID (default: 'customer_information_test').

    Returns:
    - pd.DataFrame: A pandas DataFrame containing the data from the specified BigQuery table.
    """
    # Set the environment variable for Google Cloud credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

    try:
        # Read data from the specified BigQuery table
        table_df = gbq.read_gbq(f'{project_id}.{dataset_id}.{table_id}')
        return table_df
    except Exception as e:
        # Print any exceptions that occur during the BigQuery table reading process
        print(e)


def delete_big_query_data(credentials_path='cred.json', project_id='autobot-v1-356820', dataset_id='test_247360145_247360145', table_id='customer_information_test',
                          target_column='customer_id', target_value='11330074'):
    """
    Delete data from a BigQuery table based on a condition.

    Args:
        credentials_path (str): Path to the Google Cloud credentials JSON file.
        project_id (str): Google Cloud project ID.
        dataset_id (str): BigQuery dataset ID.
        table_id (str): BigQuery table ID.
        target_column (str): Name of the column to use in the deletion condition.
        target_value (str): Value to use in the deletion condition.

    Returns:
        None
    """

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    client = bigquery.Client()
    delete_condition = f"DATE(PARSE_TIMESTAMP('%E4Y-%m-%dT%H:%M:%E*S%Ez', {target_column})) >= '{target_value}'"

    try:
        sql = f"DELETE FROM `{project_id}.{dataset_id}.{table_id}` WHERE {delete_condition}"
        query_job = client.query(sql)
        print(query_job.result())
    except Exception as e:
        print(e)

def location_to_geo(state='Virginia', city='Alexandria', user_agent='dummy'):
    """
    Converts a location (state and city) to geographical coordinates (longitude and latitude).

    Parameters:
    - state (str): The state of the location (default: 'Virginia').
    - city (str): The city of the location (default: 'Alexandria').
    - user_agent (str): User agent for the Nominatim geocoder (default: 'dummy').

    Returns:
    - tuple: A tuple containing the longitude and latitude of the specified location.
    """
    # Create a geolocator object with the specified user agent
    geolocator = Nominatim(user_agent=user_agent)

    # Create a location string in the format 'City, State'
    location = f'{city.capitalize()}, {state.capitalize()}'

    try:
        # Use the geolocator to get coordinates for the location
        coords = geolocator.geocode(location)
        return coords.longitude, coords.latitude
    except Exception as e:
        # Print any exceptions that occur during geocoding
        print(e)


def geo_to_timezone(lat, lng):
    """
    Converts geographical coordinates (latitude and longitude) to a timezone.

    Parameters:
    - lat (float): Latitude of the location.
    - lng (float): Longitude of the location.

    Returns:
    - tzinfo: timezone at the specified coordinates.
    """
    # Create a TimezoneFinder object
    tf = TimezoneFinder()

    try:
        # Get the timezone at the specified coordinates
        detected_tz = tf.timezone_at(lng=lng, lat=lat)
        # Create a timezone object based on the detected timezone
        tzinfo = pytz.timezone(str(detected_tz))
        return tzinfo
    except Exception as e:
        # Print any exceptions that occur during timezone detection
        print(e)


def utc_to_custom_tz(date_string, desired_timezone):
    """
    Converts a UTC datetime string to a desired timezone.

    Parameters:
    - date_string (str): UTC datetime string to be converted.
    - desired_timezone (str or tzinfo): Timezone to convert the datetime to. Can be either a string (e.g., 'America/New_York') or a tzinfo object.

    Returns:
    - pd.Series: A pandas Series containing the converted Date, Time, and Timezone parts.
    """
    # Check if date_string is not provided as string, convert into string
    if isinstance(date_string, str)==False and date_string != None:
        date_string = date_string.strftime("%Y-%m-%dT%H:%M:%S")

    # Check if desired_timezone is provided as a string and convert it to a tzinfo object
    if isinstance(desired_timezone, str):
        desired_timezone = pytz.timezone(desired_timezone)

    # Check for invalid or missing date strings
    if pd.isna(date_string) or date_string == 'None' or date_string == 'nan' or date_string == '' or parser.parse(date_string).date() < datetime(1800, 1, 1).date():
        date_part, time_part, timezone_part = None, None, None
        return pd.Series({'Date': date_part, 'Time': time_part, 'Timezone': timezone_part})
    else:
        # Parse the date string and convert to the desired timezone
        date_string = str(date_string)
        date_object_utc = parser.parse(date_string)
        date_object_desired_timezone = date_object_utc.replace(tzinfo=pytz.utc).astimezone(desired_timezone)

        # Extract date, time, and timezone parts
        date_part = date_object_desired_timezone.date()
        time_part = date_object_desired_timezone.timetz()
        timezone_part = date_object_desired_timezone.tzname()
        # return the converted date, time, and timezone parts
        return pd.Series({'Date': date_part, 'Time': time_part, 'Timezone': timezone_part})