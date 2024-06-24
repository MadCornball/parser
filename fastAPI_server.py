from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import os
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()

JSON_FILE_PATH = 'menu_data.json'

def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('--ignore-certificate-errors')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    chrome_version = driver.capabilities['browserVersion']
    chromedriver_version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
    print(f"Chrome version: {chrome_version}")
    print(f"Chromedriver version: {chromedriver_version}")

    return driver

async def scrape_menu(url: str) -> List[Dict[str, Any]]:
    driver = get_driver()
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cmp-category__item')))

        time.sleep(5)

        menu_items = []
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        menu_sections = soup.find_all('li', class_='cmp-category__item')

        if not menu_sections:
            raise HTTPException(status_code=404, detail="No product cards found on the page.")

        for section in menu_sections:
            item = extract_menu_item(section)
            if item:
                details = await fetch_product_details(item['link'])
                item.update(details)
                menu_items.append(item)

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during scraping: {e}")
    finally:
        driver.quit()

    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(menu_items, f, ensure_ascii=False, indent=4)

    return menu_items

def extract_menu_item(section) -> Dict[str, Any]:
    item = {}
    try:
        link = section.find('a', class_='cmp-category__item-link')
        if link and link.has_attr('href'):
            item['link'] = link['href']

        name = section.find('div', class_='cmp-category__item-name')
        if name:
            item['name'] = name.text.strip()
    except Exception as e:
        print(f"Error extracting menu item: {e}")
        return None

    return item

async def fetch_product_details(product_url: str) -> Dict[str, Any]:
    driver = get_driver()
    driver.get(product_url)

    try:
        wait = WebDriverWait(driver, 20)
        accordion_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-accordion__button')))
        accordion_button.click()

        time.sleep(2)

        html_after_click = driver.page_source
        soup = BeautifulSoup(html_after_click, 'html.parser')

        product_details = {
            "description": soup.find('div', class_='cmp-product-detail__description').text.strip() if soup.find('div', class_='cmp-product-detail__description') else "N/A",
            "calories": extract_nutrition_value(soup, 'Калорійність'),
            "fats": extract_nutrition_value(soup, 'Жири'),
            "carbs": extract_nutrition_value(soup, 'Вуглеводи'),
            "proteins": extract_nutrition_value(soup, 'Білки'),
            "unsaturated_fats": extract_nutrition_value(soup, 'Насичені жири'),
            "sugar": extract_nutrition_value(soup, 'Цукор'),
            "salt": extract_nutrition_value(soup, 'Сіль'),
            "portion": soup.find('span', class_='cmp-nutrition-summary__heading-primary-serving').text.strip() if soup.find('span', class_='cmp-nutrition-summary__heading-primary-serving') else "N/A"
        }

        return product_details

    except Exception as e:
        print(f"An error occurred while fetching product details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch product details.")
    finally:
        driver.quit()

def extract_nutrition_value(soup: BeautifulSoup, label: str) -> str:
    element = soup.find('li', class_='cmp-nutrition-summary__heading-primary-item',
                        string=lambda t: t and label in t)
    if element:
        value_element = element.find('span', class_='value')
        if value_element:
            return value_element.text.strip()
    return "N/A"

@app.get("/")
def read_root():
    return {"message": "Welcome to the McDonald's menu API. Use /all_products/ to get all product names."}

@app.get("/all_products/", response_model=List[Dict[str, Any]])
async def get_all_products():
    url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
    menu_items = await scrape_menu(url)
    if menu_items:
        return menu_items
    else:
        raise HTTPException(status_code=500, detail="Failed to load menu items from the website.")

@app.get("/products/{product_name}", response_model=Dict[str, Any])
async def get_product(product_name: str):
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        menu_items = json.load(f)

    for item in menu_items:
        if item['name'].lower() == product_name.lower():
            return item

    raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")

@app.get("/products/{product_name}/{product_field}", response_model=str)
async def get_product_field(product_name: str, product_field: str):
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        menu_items = json.load(f)

    for item in menu_items:
        if item['name'].lower() == product_name.lower():
            if product_field in item:
                return item[product_field]
            else:
                raise HTTPException(status_code=404, detail=f"Field '{product_field}' not found in product details.")

    raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
