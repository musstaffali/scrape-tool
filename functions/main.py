# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`
import sys
import os
import uuid

module_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, module_directory)
import flask
import datetime
from firebase_functions import firestore_fn, https_fn
from firebase_admin import initialize_app, firestore
from amazon_scraper import scrape_amazon_books
from author_contact_scraper import get_author_contact, extract_social_media_profiles
import google.cloud.firestore

initialize_app()

db = firestore.client()
app = flask.Flask(__name__)



@https_fn.on_request()
def store_user(user_data):
    # Extract user data
    author_name = user_data['name']
    email = user_data['email']
    social_media_profiles = user_data['social_media_profiles']
    created_date = datetime.datetime.now()

    # Create a new Firestore document for the user
    user_doc = db.collection('users').document(author_name)

    # Check if the user already exists in Firestore
    if user_doc.get().exists:
        print(f"User '{author_name}' already exists. Skipping.")
        return

    # Create a data dictionary for the user document
    user_doc_data = {
        'name': author_name,
        'email': email,
        'social_media_profiles': social_media_profiles,
        'created_date': created_date,
        'books': []  # Initialize an empty list for books
    }

    # Add the user document to Firestore
    user_doc.set(user_doc_data)
    print(f"User '{author_name}' stored in Firestore.")


# Generates and stores authors data in Firestore
@https_fn.on_request()
def generate_authors(request: flask.Request) -> flask.Response:
    try:

        # Hardcoded Amazon page URL
        amazon_url = "https://www.amazon.com/s?i=stripbooks&bbn=283155&rh=n%3A283155%2Cp_n_publication_date%3A1250227011&s=date-desc-rank&dc&ds=v1%3A31byOWupVbPc1RtieAsFRC2Z8%2BF12Vh%2BNDcURCCfBZA&qid=1684721515&rnid=1250225011&ref=sr_st_date-desc-rank"

        # Scrape the Amazon books and retrieve authors and books
        scraped_data = scrape_amazon_books(amazon_url)
        
        # If scraped_data is None or empty, return an error
        if not scraped_data:
            return flask.jsonify({'error': 'No data could be scraped from the provided URL'}), 500
        
        contact_info = []

        # Process each book and its authors
        for book, authors in scraped_data.items():
            print(f"Processing book: {book}")
            for author in authors:
                print(f"Processing author: {author}")
                if(author == ''): 
                    continue
                # Create a new Firestore document for the author map
                author_map = db.collection('author_map').document(author)

                # Check if the author already exists in Firestore
                if author_map.get().exists:
                    print(f"Author '{author}' already exists. Skipping.")
                    continue

                # Generate a new unique id for the author
                author_id = str(uuid.uuid4())
                user_doc = db.collection('authors').document(author_id)

                # Add the author to the author map
                author_map.set({'id': author_id})

                # Fetch contacts
                # contacts = get_author_contact(author)

                # emails = [contact['value'] for contact in contacts if contact['type'] == 'email']
                # social_media_profiles = [{'name': contact['name'], 'url': contact['url']} for contact in contacts if contact['type'] == 'social_media']

                user_doc.set({
                    'author': author,
                    'book': [book],
                    'created_at': firestore.SERVER_TIMESTAMP
                })

                contact_info.append(author)

        return flask.jsonify(contact_info)
    except Exception as e:
        # Handle the exception
        error_message = f"An error occurred: {str(e)}"
        # You can log the error or take appropriate action based on your requirements
        # For example, you can return an error response with a specific HTTP status code
        return flask.jsonify({'error': error_message}), 500
