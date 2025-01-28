import requests
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


def convert_datetime_to_parts(date_string, timezone_name):
    if pd.isna(date_string):
      date_part, time_part, timezone_part = None, None, None
      return pd.Series({'Date': date_part, 'Time': time_part, 'Timezone': timezone_part})
    else:
      date_string = str(date_string)
      date_time_str = date_string
      pattern = r'^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})'
      date_time_str = date_time_str.split(".")[0]

      match_ = re.match(pattern, date_time_str)
      if match_:
          date_part = match_.group(1)
          time_part = match_.group(2)
          time_part = time_part.split(".")[0]
          date_time_combined = date_part + 'T' + time_part
          # Parse the input date string into a datetime object in UTC
          date_object_utc = datetime.strptime(date_time_combined, "%Y-%m-%dT%H:%M:%S")
          date_object_utc = date_object_utc.replace(tzinfo=pytz.UTC)

          # Check if the date is smaller than '1800-01-01'
          if date_object_utc.date() < datetime(1800, 1, 1).date():
              date_object_utc = None

          if date_object_utc == None:
            date_part, time_part, timezone_part = None, None, None
            # print(date_part, time_part, timezone_part)
          else:
            # Define the desired timezone
            desired_timezone = pytz.timezone(timezone_name)

            # Convert the datetime to the desired timezone
            date_object_desired_timezone = date_object_utc.astimezone(desired_timezone)

            # Format the converted datetime as a string
            formatted_date = date_object_desired_timezone.strftime("%Y-%m-%d %H:%M:%S %Z")

            # Split the formatted_date into date, time, and timezone
            date_part, time_part, timezone_part = formatted_date.split()
            # print(date_part, time_part, timezone_part)
          return pd.Series({'Date': date_part, 'Time': time_part, 'Timezone': timezone_part})

      elif match_ == False or date_time_str == 'None' or date_time_str == 'nan':
          date_part, time_part, timezone_part = None, None, None
          return pd.Series({'Date': date_part, 'Time': time_part, 'Timezone': timezone_part})
          # print("No match found or Either value is None")


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


def delete_big_query_data(credentials_path='cred.json', project_id = 'autobot-v1-356820', dataset_id = 'test_247360145_247360145', table_id = 'customer_information_test',
    target_column = 'customer_id', target_value = '11330074'):

    credentials_path = credentials_path
    # Set the environment variable for Google Cloud credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    # Create a BigQuery client
    client = bigquery.Client()
    # Define your delete condition
    delete_condition = f"DATE(PARSE_TIMESTAMP('%E4Y-%m-%dT%H:%M:%E*S%Ez', {target_column})) >= '{target_value}'"
    # delete_condition = f"DATE(PARSE_TIMESTAMP('YYYY-MM-DD', {target_column})) >= '{target_value}'"
    try:
      # Construct the DELETE SQL statement
      sql = f"DELETE FROM `{project_id}.{dataset_id}.{table_id}` WHERE {delete_condition}"
      # Execute the SQL statement
      query_job = client.query(sql)
      # Wait for the query job to complete
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