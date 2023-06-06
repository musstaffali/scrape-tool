from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import re
from pyhunter import PyHunter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

    sanitized_author = re.sub(r'[^\w\s]', '', author)

    # Define the Google search query string
    query_string = f"{sanitized_author} author instagram OR twitter OR facebook"

    search_results = google_search(query_string)

    social_media_tags = {
        'twitter.com': 'Twitter',
        'linkedin.com': 'LinkedIn',
        'facebook.com': 'Facebook',
        'instagram.com': 'Instagram'
    }

    for item in search_results:
        link = item['link']
        for platform, name in social_media_tags.items():
            first_name, last_name = sanitized_author.lower().split()
            if platform in link and (first_name in link.lower() or last_name in link.lower()):
                social_media_profiles.append((name, link))
                break

    return social_media_profiles


def score_social_media_profile(profile_url, author_name):
    score = 1

    # Check if the profile handle or username contains the author's name
    if author_name.lower() in profile_url.lower():
        score += 1

    return score

def get_author_contact(author_name):
    queries = [
        format_query_string(author_name, "author email"),
        # format_query_string(author_name, "author contact information"),
        # format_query_string(author_name, "author website"),
        # format_query_string(author_name, "author bio"),
        # format_query_string(author_name, "author social profile"),
        # format_query_string(author_name, "author linkedin"),
        # format_query_string(author_name, "goodreads author"),
        # Add more relevant queries
    ]
    social_media_profiles = []
    contacts = []

    try:
    # Use a ThreadPoolExecutor to make the Google Search requests in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_query = {executor.submit(google_search, query): query for query in queries}
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    print(f"Error occurred while processing the query: {query}")
                    continue

                for result in results:
                    try:
                        url = result["link"]
                        try:
                            response = requests.get(url, timeout=5)
                        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                            print(f"An unexpected error occurred: {e}")
                            print(f"Error occurred for url: {url}")
                            print(e)
                            continue  # Skip the current iteration and move to the next one

                        soup = BeautifulSoup(response.content, "html.parser")
                        emails = extract_emails(soup)

                        for email in emails:
                            # score = score_email(email, author_name, None)
                            # if score > 0:
                            contacts.append(
                                {"type": "email", "value": email, "confidence": 1})

                    except HttpError as e:
                        print(
                            f"An error occurred while processing the query response url: {url}")
                        print(e)
                        # Don't return None, just continue with the next URL
    except Exception as e:
        print(f"An error occurred while executing tasks: {e}")
    
    try:
        social_media_profiles = extract_social_media_profiles(author_name)
    except Exception as e:
        print(f"An error occurred while extracting social media profiles for {author_name}: {e}")
        social_media_profiles = []

       
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
