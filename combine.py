import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import re
from pyhunter import PyHunter
from googleapiclient.discovery import build
import urllib.parse
from googleapiclient.errors import HttpError


# api codes 
cx = "c2a71ee1a90414df8"
google_api = "AIzaSyBslETljLKindUxA24f4Rln3klXpV49R5Q"
# Initialize the Hunter API client
hunter_api_key = "2f6fdf02f290f415ffed1678b84e8e61feaadd82"
hunter = PyHunter(hunter_api_key)



# code after api and before old amazon extracting python script

def format_query_string(author: str, keyword: str):
    query = f"{author} {keyword}"
    return query


def google_search(query, max_results=10):
    try:
        service = build("customsearch", "v1", developerKey=google_api)
        res = service.cse().list(q=query, cx=cx,  num=max_results).execute()
        if 'items' in res:
            return res['items']
        else:
            print(f"No results found for the query: {query}")
            return []
    except HttpError as e:
        print(f"An error occurred while processing the query: {query}")
        print(e)
        return None


def is_valid_email(email):
    email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return email_regex.match(email)


def extract_emails(soup):
    emails = []
    for mailto in soup.select('a[href^=mailto]'):
        email = mailto['href']
        if email.startswith('mailto:'):
            email = email[7:]
        if is_valid_email(email):
            emails.append(email)
    return emails


def score_email(email, author_name, book_title):
    score = 0
    email_parts = email.split('@')[0].split('.')
    author_parts = author_name.lower().split(' ')

    for part in author_parts:
        if part in email_parts:
            score += 1

    if book_title:
        book_parts = book_title.lower().split(' ')
        for part in book_parts:
            if part in email_parts:
                score += 0.5

    return score


def get_author_contact(author_name):
    queries = [
        format_query_string(author_name, "email"),
        format_query_string(author_name, "contact"),
        format_query_string(author_name, "author site"),
        format_query_string(author_name, "author bio"),
        format_query_string(author_name, "author profile"),
        format_query_string(author_name, "linkedin"),
        format_query_string(author_name, "goodreads author"),
        # format_query_string(author_name, "blog"),
        # format_query_string(author_name, "publisher"),
    ]

    emails = []

    for query in queries:
        results = google_search(query)
        if results is None:
            print(f"Error occurred while processing the query: {query}")
            continue

        for result in results:
            try:
                url = result["link"]
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")
                emails.extend(extract_emails(soup))
            except HttpError as e:
                print(
                    f"An error occurred while processing the query response url: {url}")
                print(e)
                return None

    scored_emails = [(email, score_email(email, author_name, None))
                     for email in emails]
    scored_emails.sort(key=lambda x: x[1], reverse=True)

    return scored_emails

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


