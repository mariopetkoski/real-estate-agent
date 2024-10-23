import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

PAGES_MAX = 2


def get_links(response) -> list:
    hrefs = []
    for page in tqdm(range(1, PAGES_MAX + 1)):
        url_all = f'https://www.pazar3.mk/ads/real-estate/for-sale?Page={page}'
        response = requests.get(url_all)
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links with a specific class (like "SearchAdTitle")
            links = soup.find_all('a', class_='Link_vis')

            # Extract the href attributes from the links
            hrefs.extend([link.get('href') for link in links])

        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    print(len(hrefs))
    return hrefs


def get_property_values(url):
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')

        # Title
        title = soup.find('h1', class_='ci-text-base').text.strip() if soup.find('h1', class_='ci-text-base') else ""

        # Price, Currency
        price_class = soup.find('h4', class_='ci-text-success')
        price = price_class.find('span').get('value') if price_class and price_class.find('span') else ""
        currency = price_class.find_all('span')[1].text.strip() if price_class and len(
            price_class.find_all('span')) > 1 else ""

        # Initialize the fields
        number_of_rooms = ""
        area = ""
        location = ""

        # Tags Area
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


if __name__ == '__main__':
    URL = 'https://www.pazar3.mk/ads/real-estate/for-sale/skopje'
    PAGE = 1

    response = requests.get(URL)

    links = get_links(response)

    dataframe = pd.DataFrame(columns=['Title', 'Price', 'Currency', 'Number_of_rooms', 'Area', 'Location'])

    for link in tqdm(links):
        row = get_property_values('https://www.pazar3.mk' + link)
        dataframe = dataframe._append(row, ignore_index=True)

    print(dataframe.head())
