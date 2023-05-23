import uuid
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from firebase_admin import initialize_app, firestore, credentials

cred = credentials.Certificate("service_account.json")
initialize_app(cred)

db = firestore.client()


def scrape_amazon_books(amazon_url):
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
    #     'Accept-Language': 'en-US, en;q=0.5'
    # }
   # Setup WebDriver options
    options = webdriver.ChromeOptions()
    # Add headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    options.add_argument(f"user-agent={headers['User-Agent']}")
    options.add_argument(f"accept-language={headers['Accept-Language']}")

    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Set up the Service object
    s=Service(ChromeDriverManager().install())
    
    # Load the webpage
    driver = webdriver.Chrome(service=s, options=options)
    
    # Extract the source of the page
    driver.get(amazon_url)
    page_source = driver.page_source
    
    # Close the browser
    driver.quit()

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # response = requests.get(amazon_url, headers=headers)
    # if response.status_code == 503:
    #     raise Exception("503 Service Unavailable error. Retry after a while.")

    # soup = BeautifulSoup(response.content, 'html.parser')

    results = soup.find_all('div', {
                            'class': 'a-section a-spacing-none puis-padding-right-small s-title-instructions-style'})
    total_results = {}

    for result in results:
        book_title_element = result.find(
            'span', {'class': 'a-size-medium a-color-base a-text-normal'})
        book_title = book_title_element.text.strip() if book_title_element else ''

        author_elements = result.find_all('span', {'class': 'a-size-base'})
        author_names = []
        include_author_names = False  # Flag to indicate when to start including author names
        for author_element in author_elements:
            author_text = author_element.text.strip()
            if author_text.lower() == 'by':
                include_author_names = True
            elif include_author_names:
                author_link = author_element.find('a')
                if author_link:
                    author_name = author_link.text.strip()
                    author_names.append(author_name)
                else:
                    author_text = author_element.text.strip()
                    if not re.search(r'\d', author_text) and author_text.lower() not in ['by', '|', 'and', ',', 'et al']:
                        author_names.append(author_text)

                # Additional handling for the case where author name is wrapped in a <div> element
                if not author_names:
                    author_div = result.find(
                        'div', {'class': 'a-row a-size-base a-color-secondary'})
                    if author_div:
                        author_link = author_div.find('a')
                        if author_link:
                            author_name = author_link.text.strip()
                            author_names.append(author_name)
                        else:
                            author_text = author_div.text.strip()
                            if not re.search(r'\d', author_text) and author_text.lower() not in ['by', '|', 'and', ]:
                                author_names.append(author_text)

        total_results[book_title] = author_names

    return total_results

def store_authors():
    try:

        # Hardcoded Amazon page URL
        amazon_url = "https://www.amazon.com/s?i=stripbooks&bbn=283155&rh=n%3A283155%2Cp_n_publication_date%3A1250227011&s=date-desc-rank&dc&ds=v1%3A31byOWupVbPc1RtieAsFRC2Z8%2BF12Vh%2BNDcURCCfBZA&qid=1684721515&rnid=1250225011&ref=sr_st_date-desc-rank"

        # Scrape the Amazon books and retrieve authors and books
        scraped_data = scrape_amazon_books(amazon_url)
        
        # If scraped_data is None or empty, return an error
        if not scraped_data:
            return {'error': 'No data found'}
        
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

        return {'message': 'Authors stored successfully', 'authors': contact_info}
    except Exception as e:
        # Handle the exception
        error_message = f"An error occurred: {str(e)}"
        # You can log the error or take appropriate action based on your requirements
        # For example, you can return an error response with a specific HTTP status code
        return {'error': error_message}


store_authors()