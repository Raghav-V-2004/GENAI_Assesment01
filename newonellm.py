import time
import requests
import pandas as pd, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import cohere


api_key = <API_KEY>
co = cohere.Client(api_key)


base_urls = [
    "https://about.linkedin.com/",
    "https://www.salesforce.com/",
    "https://www.basf.com/",
    "https://www.morganstanley.com/",
    "https://www.alibaba.com/",
    "https://www.mobility.siemens.com/",
    "https://www.gm.com/",
    #"https://www.ebay.com"
    #https://about.twitter.com
    #https://www.marriott.com
    #These 3 sites blocked by jman
]

visited_urls = set()
csv_filename = "C:/Users/RaghavV/Downloads/extracted_company_info.csv"
data = []


def extract_info_with_cohere(text):
    prompt = f"""
    Extract the following details from the provided text:
    1. What is the company's mission statement or core values?
    2. What products or services does the company offer?
    3. When was the company founded, and who were the founders?
    4. Where is the company's headquarters located?
    5. Who are the key executives or leadership team members?
    6. Has the company received any notable awards or recognitions?

    Text: {text}
    """

    response = co.chat(
        message=prompt,
        model="command-xlarge-nightly",
        temperature=0.5,
    )
    return response.text.strip()


def get_soup(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def normalize_url(url):
    """Removes fragment (#) and normalizes the URL."""
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

def get_nav_and_footer_links(soup, base_url):
    """Extracts all links from navbar and footer."""
    links = set()
    for tag in soup.select("nav a, footer a"):
        href = tag.get("href")
        if href:
            full_url = normalize_url(urljoin(base_url, href))
            if full_url.startswith(base_url):
                links.add(full_url)
    return links


def scrape_page(url, base_url, company_content):
    normalized_url = normalize_url(url)
    if normalized_url in visited_urls:
        return company_content

    print(f"Visiting: {normalized_url}")
    visited_urls.add(normalized_url)

    soup = get_soup(url)
    if not soup:
        return company_content

  
    page_text = soup.get_text(separator=" ", strip=True)
    company_content += " " + page_text

  
    new_links = get_nav_and_footer_links(soup, base_url)
    for link in new_links:
        if normalize_url(link) not in visited_urls:
            company_content = scrape_page(link, base_url, company_content)

    return company_content


def main():
    results = []

 
    for base_url in base_urls:
        print(f"\n--- Scraping content for {base_url} ---")
        company_content = scrape_page(base_url, base_url, "")
        
        print("Sending content to Cohere for extraction...")
        extracted_info = extract_info_with_cohere(company_content)

      
        results.append({
            "Base URL": base_url,
            "Extracted Information": extracted_info
        })

 
    df = pd.DataFrame(results)
    df.to_csv(csv_filename, index=False)
    print(f"Data saved to {csv_filename}.")

if __name__ == "__main__":
    main()
