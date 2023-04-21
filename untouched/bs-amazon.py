import re
from bs4 import BeautifulSoup
import requests
import csv
from pyhunter import PyHunter
from googleapiclient.discovery import build
import urllib.parse
from googleapiclient.errors import HttpError

cx = "c2a71ee1a90414df8"
google_api = "AIzaSyBslETljLKindUxA24f4Rln3klXpV49R5Q"
# Initialize the Hunter API client
hunter_api_key = "2f6fdf02f290f415ffed1678b84e8e61feaadd82"
hunter = PyHunter(hunter_api_key)


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


# get html
url = "https://www.amazon.com/Best-Sellers-Books/zgbs/books"

# change the user-agent value based on your web browser
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'}

page = requests.get(url, headers=headers)

soup = BeautifulSoup(page.content, 'html.parser')

# get all books
books = soup.find_all(id="gridItemRoot")

csv_headers = ['Rank', 'Title', 'Author', 'Description']
with open('amazon_books.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)

testing = books[:1]
for book in testing:

    rank = book.find('span', class_='zg-bdg-text').text[1:]

    children = book.find('div', class_='zg-grid-general-faceout').div

    title = children.contents[1].text
    author = children.contents[2].text
    desc = children.contents[4].text.strip()

    # Define the Google search query string
    query_string = f"{author} author instagram OR twitter OR facebook"

    # Define the Google search URL and headers
    googleUrl = "https://www.google.com/search"

    # Make the Google search request and parse the HTML using BeautifulSoup
    response = requests.get(googleUrl, headers=headers,
                            params={"q": query_string})
    soupGoogle = BeautifulSoup(response.text, "html.parser")

    # Extract the search result titles and URLs using BeautifulSoup
    search_results = soupGoogle.select(".tF2Cxc")

    # Filter the search results to only include social media profiles
    social_media_profiles = []
    emails = []
    email_scores = []
    for result in search_results:
        if "instagram.com" in result.a["href"] or "twitter.com" in result.a["href"] or "facebook.com" in result.a["href"]:
            social_media_profiles.append((result.a.text, result.a["href"]))

    contact_info = get_author_contact(author)

    if contact_info:
        print(f"Contact information for {author}:")
        for email, score in contact_info:
            emails.append(email)
            email_scores.append(score)
            print(f"{email} (Confidence: {score})")

    else:
        print(f"Could not find contact information for {author}.")

    with open('amazon_books.csv', 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([rank, title, author, desc,
                        social_media_profiles, emails, email_scores])
