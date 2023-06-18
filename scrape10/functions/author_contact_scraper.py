import requests
from bs4 import BeautifulSoup
import re
from pyhunter import PyHunter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# API codes
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
        res = service.cse().list(q=query, cx=cx, num=max_results).execute()
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

    # Additional criteria for email scoring
    if author_name.lower() in email.lower():
        score += 1

    return score


def extract_social_media_profiles(author):
    print(f"Extracting social media profiles for {author}")
    social_media_profiles = []

    # Define the Google search query string
    query_string = f"{author} author instagram OR twitter OR facebook"

    search_results = google_search(query_string)

    social_media_tags = {
        'twitter.com': 'Twitter',
        'linkedin.com': 'LinkedIn',
        'facebook.com': 'Facebook',
        'instagram.com': 'Instagram'
        # Add more social media platforms as needed
    }

    for item in search_results:
        link = item['link']
        for platform, name in social_media_tags.items():
            if platform in link:
                social_media_profiles.append((name, link))
                break

    return social_media_profiles


def score_social_media_profile(profile_url, author_name):
    score = 0

    # Check if the profile handle or username contains the author's name
    if author_name.lower() in profile_url.lower():
        score += 1

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
        # Add more relevant queries
    ]

    try:
        social_media_profiles = extract_social_media_profiles(author_name)
    except Exception as e:
        print(f"An error occurred while extracting social media profiles for {author_name}: {e}")
        social_media_profiles = []

    contacts = []

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
                emails = extract_emails(soup)

                for email in emails:
                    score = score_email(email, author_name, None)
                    if score > 0:
                        contacts.append(
                            {"type": "email", "value": email, "confidence": score})

            except HttpError as e:
                print(
                    f"An error occurred while processing the query response url: {url}")
                print(e)
                return None
    
    for profile_name, profile_url in social_media_profiles:
        score = score_social_media_profile(
            profile_url, author_name)
        if score > 0:
            contacts.append(
                {"type": "social_media", "name": profile_name, "url": profile_url, "confidence": score})
            
    contacts.sort(key=lambda x: x['confidence'], reverse=True)
    valid_contacts = [
        contact for contact in contacts if contact['confidence'] > 0]

    return valid_contacts


def scrape_amazon_books(date_filter=None):
    base_url = "https://www.amazon.com"
    search_url = f"{base_url}/s?k=books"

    if date_filter:
        # Format the date filter as YYYY-MM-DD
        start_date = date_filter[0].strftime("%Y-%m-%d")
        end_date = date_filter[1].strftime("%Y-%m-%d")
        search_url += f"&rh=p_n_date:{start_date}-{end_date}"

    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract book information from the search results
    books = soup.select("div[data-asin]")

    for book in books:
        # Extract the book details
        title = book.select_one("span.a-size-medium.a-color-base.a-text-normal").text.strip()
        author = book.select_one("span.a-size-base+ .a-size-base").text.strip()
        price = book.select_one(".a-offscreen")
        price = price.text.strip() if price else "Not available"

        print("Title:", title)
        print("Author:", author)
        print("Price:", price)

        # Get author contact information
        contacts = get_author_contact(author)
        if contacts:
            print("Contact Information:")
            for contact in contacts:
                if contact['type'] == 'email':
                    print("Email:", contact['value'])
                elif contact['type'] == 'social_media':
                    print(f"{contact['name']} Profile:", contact['url'])
            print()

        print()


# Example usage
start_date = input("Enter the start date (YYYY-MM-DD) for filtering (optional): ")
end_date = input("Enter the end date (YYYY-MM-DD) for filtering (optional): ")

date_filter = None
if start_date and end_date:
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    date_filter = (start_date, end_date)

scrape_amazon_books(date_filter)
