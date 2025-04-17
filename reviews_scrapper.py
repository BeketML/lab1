from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pandas as pd
import json

# Review <div class="_1k5soqfl">

def get_full_html():
    driver = webdriver.Chrome()
    url = 'https://2gis.kz/almaty/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/firm/70000001021663285/76.828986%2C43.225603/tab/reviews?m=76.89413%2C43.242883%2F11.79'
    
    try:
        driver.get(url)
        print("Loading page...")
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 30)
        
        # Wait for reviews container to be visible
        reviews_container = wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, '_1k5soqfl'
        )))
        
        # Get initial number of reviews
        current_reviews = driver.find_elements(By.CLASS_NAME, '_1k5soqfl')
        print(f"Initial number of reviews: {len(current_reviews)}")
        
        # Scroll to load all content
        print("Scrolling to load all content...")
        last_review_count = len(current_reviews)
        scroll_attempts = 0
        max_scroll_attempts = 1000
        no_new_reviews_count = 0
        max_no_new_reviews = 10  # Increased from 5 to 10
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll down smoothly
            driver.execute_script("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            time.sleep(2)  # Increased wait time to 2 seconds
            
            # Get current number of reviews
            current_reviews = driver.find_elements(By.CLASS_NAME, '_1k5soqfl')
            current_review_count = len(current_reviews)
            
            print(f"Scroll attempt {scroll_attempts}/{max_scroll_attempts}")
            print(f"Current number of reviews: {current_review_count}")
            
            # Check if we got new reviews
            if current_review_count == last_review_count:
                no_new_reviews_count += 1
                if no_new_reviews_count >= max_no_new_reviews:
                    print(f"No new reviews after {max_no_new_reviews} attempts, stopping...")
                    break
            else:
                no_new_reviews_count = 0  # Reset counter if we got new reviews
            
            last_review_count = current_review_count
            scroll_attempts += 1
        
        # Get the full HTML content
        html_content = driver.page_source
        
        # Save HTML to file
        with open('2gis_reviews.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML content saved to 2gis_reviews.html")
        
        return html_content
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    finally:
        driver.quit()

def parse_reviews(html_content):
    if not html_content:
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    reviews_data = []
    
    # Find all review containers
    review_containers = soup.find_all('div', class_='_1k5soqfl')
    print(f"Found {len(review_containers)} reviews")
    
    for review in review_containers:
        try:
            # Extract review text - try different possible selectors
            review_text = None
            text_selectors = [
                review.find('a', class_='_1wlx08h'),
                review.find('div', class_='_49x36f').find('a') if review.find('div', class_='_49x36f') else None,
                review.find('div', class_='_49x36f').find('div') if review.find('div', class_='_49x36f') else None
            ]
            
            for selector in text_selectors:
                if selector and selector.text.strip():
                    review_text = selector.text.strip()
                    break
            
            if not review_text:
                continue
            
            # Extract rating - try different possible selectors
            rating = 0
            rating_selectors = [
                review.find_all('svg', attrs={'fill': '#ffb81c'}),
                review.find_all('svg', attrs={'fill': '#FFB81C'}),
                review.find_all('div', class_='_1fkin5c')
            ]
            
            for selector in rating_selectors:
                if selector:
                    rating = len(selector)
                    if rating > 0:
                        break
            
            # Extract date - try different possible selectors
            date = None
            date_selectors = [
                review.find('div', class_='_a5f6uz'),
                review.find('div', class_='_1wlx08h').find_next_sibling('div') if review.find('div', class_='_1wlx08h') else None
            ]
            
            for selector in date_selectors:
                if selector and selector.text.strip():
                    date = selector.text.strip()
                    break
            
            if not date:
                date = "Дата не указана"
            
            # Extract author name - try different possible selectors
            author = None
            author_selectors = [
                review.find('span', class_='_16s5yj36'),
                review.find('div', class_='_1wlx08h').find_previous('span') if review.find('div', class_='_1wlx08h') else None
            ]
            
            for selector in author_selectors:
                if selector and selector.text.strip():
                    author = selector.text.strip()
                    break
            
            if not author:
                author = "Анонимный пользователь"
            
            reviews_data.append({
                'author': author,
                'rating': rating,
                'date': date,
                'review_text': review_text
            })
            
        except Exception as e:
            print(f"Error parsing review: {e}")
            continue
    
    # Save to CSV
    df = pd.DataFrame(reviews_data)
    df.to_csv('reviews.csv', index=False, encoding='utf-8')
    
    # Save to JSON
    with open('reviews.json', 'w', encoding='utf-8') as f:
        json.dump(reviews_data, f, ensure_ascii=False, indent=4)
    
    print(f"\nSuccessfully parsed {len(reviews_data)} reviews")
    print("Data saved to:")
    print("1. reviews.csv")
    print("2. reviews.json")
    
    # Print first few reviews as example
    print("\nSample reviews:")
    for i, review in enumerate(reviews_data[:3], 1):
        print(f"\nReview {i}:")
        print(f"Author: {review['author']}")
        print(f"Rating: {review['rating']} stars")
        print(f"Date: {review['date']}")
        print(f"Text: {review['review_text']}")

if __name__ == "__main__":
    html_content = get_full_html()
    parse_reviews(html_content)