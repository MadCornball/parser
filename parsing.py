from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import os
import json
import requests
from bs4 import BeautifulSoup

app = FastAPI()

JSON_FILE_PATH = 'menu_data.json'
BASE_URL = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "sec-ch-ua": '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Referer": "https://www.mcdonalds.com/ua/uk-ua/product/"
}

def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

def parse_menu(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, 'html.parser')
    menu_items = []

    menu_sections = soup.find_all('li', class_='cmp-category__item')
    if not menu_sections:
        raise HTTPException(status_code=404, detail="No product cards found on the page.")

    for section in menu_sections:
        item = extract_menu_item(section)
        if item:
            menu_items.append(item)

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
    html = fetch_html(product_url)
    soup = BeautifulSoup(html, 'html.parser')

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

def extract_nutrition_value(soup: BeautifulSoup, label: str) -> str:
    element = soup.find('li', class_='cmp-nutrition-summary__heading-primary-item', string=lambda t: t and label in t)
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
    html = fetch_html(BASE_URL)
    menu_items = parse_menu(html)
    if menu_items:
        for item in menu_items:
            details = await fetch_product_details(item['link'])
            item.update(details)

        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(menu_items, f, ensure_ascii=False, indent=4)

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
    uvicorn.run(app, host="127.0.0.1", port=8001)
