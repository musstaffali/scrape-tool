from functions.amazon_scraper import scrape_amazon_books
from functions.author_contact_scraper import get_author_contact, extract_social_media_profiles

amazon_url = "https://www.amazon.com/s?i=stripbooks&bbn=283155&rh=n%3A283155%2Cp_n_publication_date%3A1250227011&s=date-desc-rank&dc&ds=v1%3A31byOWupVbPc1RtieAsFRC2Z8%2BF12Vh%2BNDcURCCfBZA&qid=1684721515&rnid=1250225011&ref=sr_st_date-desc-rank"

# Call the scraping function
result_map = scrape_amazon_books(amazon_url)


print(result_map)
