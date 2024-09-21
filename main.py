import json
import csv
import time
import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Selenium WebDriver with retries
def init_driver(retries=3):
    attempt = 0
    while attempt < retries:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--log-level=3')
            driver = webdriver.Chrome(options=options)
            logging.info("WebDriver initialized successfully")
            return driver
        except WebDriverException as e:
            attempt += 1
            logging.error(f"WebDriver initialization attempt {attempt} failed. Retrying... ({e})")
            time.sleep(2)
    raise Exception("Failed to initialize WebDriver after multiple attempts")

# Navigate to Google Lens with retries
def navigate_to_lens(driver, image_url, timeout=60, retries=1):
    lens_url = f'https://lens.google.com/uploadbyurl?url={image_url}'
    attempt = 0
    while attempt < retries:
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(lens_url)
            logging.info(f"Successfully navigated to {lens_url}")
            return True
        except TimeoutException:
            attempt += 1
            logging.error(f"Timeout loading {lens_url}, retry {attempt}/{retries}")
            time.sleep(2)
        except Exception as e:
            attempt += 1
            logging.error(f"Could not navigate to {lens_url}, retry {attempt}/{retries}. {e}")
            time.sleep(2)
    return False

# Detect if Google Lens shows "No image at that URL" error
def check_no_image_error(driver):
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'No image at that URL')]"))
        )
        if error_message:
            logging.error("No image found at the URL.")
            return True
    except TimeoutException:
        return False
    return False

# Wait for the 'Find image source' button and click it with retries
def wait_and_click_find_image_source(driver, retries=1):
    button_selector = 'button.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-INsAgc'
    attempt = 0
    while attempt < retries:
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, button_selector))
            ).click()
            logging.info("Clicked 'Find image source' button")
            return True
        except Exception as e:
            attempt += 1
            logging.error(f"Could not click the 'Find image source' button, retry {attempt}/{retries}. {e}")
            time.sleep(2)
    return False

# Extract metadata for the first image with retries
def extract_first_image_metadata(driver, retries=1):
    attempt = 0
    while attempt < retries:
        try:
            element = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.anSuc a.GZrdsf'))
            )

            title = element.find_element(By.CSS_SELECTOR, '.iJmjmd').text if element.find_element(By.CSS_SELECTOR, '.iJmjmd') else None
            source = element.find_element(By.CSS_SELECTOR, '.ShWW9').text if element.find_element(By.CSS_SELECTOR, '.ShWW9') else None
            link = element.get_attribute('href')

            logging.info("Successfully extracted metadata")
            return {
                'position': 1,
                'title': title,
                'source': source,
                'link': link,
            }
        except Exception as e:
            attempt += 1
            logging.error(f"Could not extract metadata, retry {attempt}/{retries}. {e}")
            time.sleep(2)
    return None

# Get metadata for an image using Google Lens
def get_first_image_metadata(image_url):
    driver = init_driver()
    try:
        if not navigate_to_lens(driver, image_url):
            return None
        
        if check_no_image_error(driver):
            return None
        
        if not wait_and_click_find_image_source(driver):
            return None
        
        return extract_first_image_metadata(driver)
    finally:
        driver.quit()

# Lock for thread-safe CSV writing
csv_lock = Lock()

# Function to process each image and save metadata to CSV
def process_image(image_id, image_url, csv_file_path):
    image_data = get_first_image_metadata(image_url)
    if not image_data:
        logging.error(f"No data for image {image_id}.")
        return None

    # Prepare data for CSV
    return {
        'id': image_id, 
        'url': image_url, 
        'position': image_data.get('position', 'N/A'), 
        'title': image_data.get('title', 'N/A'), 
        'source': image_data.get('source', 'N/A'), 
        'link': image_data.get('link', 'N/A')
    }

# Process each image in parallel using ThreadPoolExecutor
def process_images_concurrently(urls_data, csv_file_path, max_workers):
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, image_id, image_url, csv_file_path) for image_id, image_url in urls_data.items()]

        all_data = []
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_data.append(result)

    # Write all the results at once for efficiency
    with csv_lock:
        with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['id', 'url', 'position', 'title', 'source', 'link'])
            writer.writerows(all_data)

# Main entry point
def main():
    parser = argparse.ArgumentParser(description="Process images using Google Lens and save metadata to CSV.")
    parser.add_argument("json_file_path", help="Path to the JSON file containing image URLs.")
    parser.add_argument("csv_file_path", help="Path to the output CSV file.")
    parser.add_argument("max_workers", help="Work in parallel", default=5, type=int)

    args = parser.parse_args()

    # Load image URLs from the JSON file
    with open(args.json_file_path, 'r') as file:
        urls_data = json.load(file)

    # CSV file setup: write header
    with open(args.csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['id', 'url', 'position', 'title', 'source', 'link'])
        writer.writeheader()

    # Process the images
    process_images_concurrently(urls_data, args.csv_file_path, args.max_workers)
    logging.info("All data saved to CSV.")

if __name__ == "__main__":
    main()
