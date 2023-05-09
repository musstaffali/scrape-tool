import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
    'Accept-Language': 'en-US, en;q=0.5'
}

search_query = 'books'.replace(' ', '+')
base_url = 'https://www.amazon.com/s?k=books&i=stripbooks&sprefix=b%2Cstripbooks%2C266&ref=nb_sb_ss_ts-doa-p_1_1'.format(search_query)

items = []
for i in range(1, 5):
    print('Processing {0}...'.format(base_url + '&page={0}'.format(i)))
    response = requests.get(base_url + '&page={0}'.format(i), headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    results = soup.find_all('div', {'class': 's-result-item', 'data-component-type': 's-search-result'})

    for result in results:
        rank_element = result.find('span', {'class': 's-main-slot'})
        rank = rank_element.text.strip() if rank_element else 'N/A'

        product_name = result.h2.text

        try:
            author = result.find('a', {'class': 'a-size-base a-link-normal'}).text.strip()
        except AttributeError:
            author = 'N/A'

        description = result.find('span', {'class': 'a-size-base-plus a-color-base a-text-normal'}).text.strip()

        try:
            price1 = result.find('span', {'class': 'a-price-whole'}).text
            price2 = result.find('span', {'class': 'a-price-fraction'}).text
            price = float(price1 + price2)
            product_url = 'https://amazon.com' + result.h2.a['href']
            items.append([rank, product_name, author, description])
        except AttributeError:
            continue
    sleep(1.5)
    
df = pd.DataFrame(items, columns=['rank', 'product', 'author', 'description'])
df.to_csv('{0}.csv'.format(search_query), index=False)
