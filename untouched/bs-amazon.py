from bs4 import BeautifulSoup
import requests
import csv
from pyhunter import PyHunter

# Initialize the Hunter API client
hunter_api_key = "2f6fdf02f290f415ffed1678b84e8e61feaadd82"
hunter = PyHunter(hunter_api_key)

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


for book in books:

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
    for result in search_results:
        if "instagram.com" in result.a["href"] or "twitter.com" in result.a["href"] or "facebook.com" in result.a["href"]:
            social_media_profiles.append((result.a.text, result.a["href"]))

    with open('amazon_books.csv', 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([rank, title, author, desc, social_media_profiles])
