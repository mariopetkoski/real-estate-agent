import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime
import psycopg2
import hashlib

PAGES_MAX = 2
# TODO: ENV VAR PAGES_MAX

def get_links(**kwargs) -> list:
    hrefs = []
    for page in tqdm(range(1, PAGES_MAX + 1)):
        url_all = f'https://www.pazar3.mk/ads/real-estate/for-sale?Page={page}'
        response = requests.get(url_all)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='Link_vis')
            hrefs.extend([link.get('href') for link in links])
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    print(len(hrefs))

    kwargs['ti'].xcom_push(key='property_links', value=hrefs)


def get_property_values(url):
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')

        title = soup.find('h1', class_='ci-text-base').text.strip() if soup.find('h1', class_='ci-text-base') else ""
        price_class = soup.find('h4', class_='ci-text-success')
        price = price_class.find('span').get('value') if price_class and price_class.find('span') else ""
        currency = price_class.find_all('span')[1].text.strip() if price_class and len(
            price_class.find_all('span')) > 1 else ""

        number_of_rooms = ""
        area = ""
        location = ""

        tags = soup.find_all('div', class_='tags-area')
        for tag in tags:
            a_tags = tag.find_all('a', class_='tag-item')
            for a in a_tags:
                label = a.find('span').text.strip() if a.find('span') else ""
                value = a.find('bdi').text.strip() if a.find('bdi') else ""
                if 'Number of rooms' in label:
                    number_of_rooms = value
                elif 'Area' in label:
                    area = value + " m²"
                elif 'Location' in label:
                    location = value

        property_data = {
            'Title': title,
            'Price': price,
            'Currency': currency,
            'Number_of_rooms': number_of_rooms,
            'Area': area,
            'Location': location
        }
        return property_data
    else:
        print(f"Failed to retrieve the page. Status code: {r.status_code}")
        return {}


def extract_property_data(**kwargs):
    links = kwargs['ti'].xcom_pull(key='property_links', task_ids='fetch_links')
    dataframe = pd.DataFrame(columns=['Title', 'Price', 'Currency', 'Number_of_rooms', 'Area', 'Location'])

    for link in tqdm(links):
        row = get_property_values('https://www.pazar3.mk' + link)
        dataframe = dataframe._append(row, ignore_index=True)

    # Store dataframe in XCom for transformation task
    kwargs['ti'].xcom_push(key='raw_dataframe', value=dataframe.to_dict())


def transform_property_data(**kwargs):
    # Retrieve the dataframe from XCom
    dataframe_dict = kwargs['ti'].xcom_pull(key='raw_dataframe', task_ids='extract_property_data')
    dataframe = pd.DataFrame.from_dict(dataframe_dict)

    # Perform the transformations
    dataframe['Area(m2)'] = dataframe['Area'].str.extract(r'(\d+)')
    dataframe.drop(columns=['Area'], inplace=True)

    dataframe['Price'] = pd.to_numeric(dataframe['Price'], errors='coerce')
    dataframe['Area(m2)'] = pd.to_numeric(dataframe['Area(m2)'], errors='coerce')
    dataframe['Number_of_rooms'] = pd.to_numeric(dataframe['Number_of_rooms'], errors='coerce')

    # print(dataframe.head())
    print(dataframe.info())

    # Optionally save the transformed dataframe or store it for further tasks
    kwargs['ti'].xcom_push(key='transformed_dataframe', value=dataframe.to_dict())

    # TODO:
    # hash, duplicates, outliers etc...

def write_to_db(**kwargs):
    # Fetch the transformed dataframe from XCom
    dataframe_dict = kwargs['ti'].xcom_pull(key='transformed_dataframe', task_ids='transform_property_data')
    dataframe = pd.DataFrame.from_dict(dataframe_dict)

    # connection = BaseHook.get_connection('postgres_connection')  # Replace with your actual connection ID

    # Create a connection to the PostgreSQL database
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        database="properties",
        user="airflow",
        password="airflow"
    )

    cursor = conn.cursor()

    # Insert data into the database
    insert_query = """
        INSERT INTO real_estate_listings (Title, Price, Currency, Number_of_rooms, Area_m2, Location)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

    for index, row in dataframe.iterrows():
        cursor.execute(insert_query, (
            row['Title'],
            row['Price'],
            row['Currency'],
            row['Number_of_rooms'],
            row['Area(m2)'],
            row['Location']
        ))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    print("Data successfully written to the database")



# Define the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1
}

with DAG('property_data_scraper', default_args=default_args, schedule_interval='@daily', catchup=False) as dag:
    fetch_links = PythonOperator(
        task_id='fetch_links',
        python_callable=get_links,
        provide_context=True
    )

    extract_data = PythonOperator(
        task_id='extract_property_data',
        python_callable=extract_property_data,
        provide_context=True
    )

    transform_data = PythonOperator(
        task_id='transform_property_data',
        python_callable=transform_property_data,
        provide_context=True
    )

    write_data_to_db = PythonOperator(
        task_id='write_data_to_db',
        python_callable=write_to_db,
        provide_context=True
    )

    fetch_links >> extract_data >> transform_data >> write_data_to_db
