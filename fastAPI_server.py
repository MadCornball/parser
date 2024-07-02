from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import json
import requests
import os

app = FastAPI()

JSON_FILE_PATH = 'menu_data.json'
BASE_URL = 'https://www.mcdonalds.com'
FULL_MENU_URL = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
HEADERS = {
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
	"sec-ch-ua": '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
	"sec-ch-ua-mobile": "?0",
	"sec-ch-ua-platform": '"macOS"',
	"Referer": "https://www.mcdonalds.com/ua/uk-ua/product/"
}

# Global variable to store menu items data
menu_items_data = None


# Function to load menu data from JSON file
def load_menu_data():
	global menu_items_data
	if not menu_items_data:
		if os.path.exists(JSON_FILE_PATH):
			with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
				menu_items_data = json.load(f)
		else:
			menu_items_data = []


# Function to save menu data to JSON file
def save_menu_data():
	global menu_items_data
	if menu_items_data:
		with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
			json.dump(menu_items_data, f, ensure_ascii=False, indent=4)


def fetch_html(url: str) -> str:
	response = requests.get(url, headers=HEADERS)
	response.raise_for_status()
	return response.text


def parse_menu(html: str) -> List[Dict[str, Any]]:
	from bs4 import BeautifulSoup
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
			item['link'] = BASE_URL + link['href']
		
		name = section.find('div', class_='cmp-category__item-name')
		if name:
			item['name'] = name.text.strip()
		
		item_id = section['data-product-id'] if 'data-product-id' in section.attrs else None
		if item_id:
			item['id'] = item_id
	except Exception as e:
		print(f"Error extracting menu item: {e}")
		return None
	
	return item


async def fetch_product_details_ajax(product_id: str) -> Dict[str, Any]:
	ajax_url = f"https://www.mcdonalds.com/dnaapp/itemDetails?country=UA&language=uk&showLiveData=true&item={product_id}"
	response = requests.get(ajax_url, headers=HEADERS)
	response.raise_for_status()
	data = response.json()
	
	if 'item' in data and data['item']:
		item = data['item']
		product_details = {
			"name": item.get('item_name', 'N/A'),
			"description": item.get('description', 'N/A'),
			"calories": next((nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if
			                  nutrient['name'] == 'Калорійність'), 'N/A'),
			"fats": next(
				(nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if nutrient['name'] == 'Жири'),
				'N/A'),
			"carbs": next((nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if
			               nutrient['name'] == 'Вуглеводи'), 'N/A'),
			"proteins": next(
				(nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if nutrient['name'] == 'Білки'),
				'N/A'),
			"unsaturated_fats": next(
				(nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if nutrient['name'] == 'НЖК'),
				'N/A'),
			"sugar": next(
				(nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if nutrient['name'] == 'Цукор'),
				'N/A'),
			"salt": next(
				(nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if nutrient['name'] == 'Сіль'),
				'N/A'),
			"portion": next((nutrient['value'] for nutrient in item['nutrient_facts']['nutrient'] if
			                 nutrient['name'] == 'Вага порції'), 'N/A'),
			"ingredients": item.get('item_ingredient_statement', 'N/A'),
			"allergens": item.get('item_allergen', 'N/A')
		}
		return product_details
	
	raise HTTPException(status_code=404, detail="Product details not found in AJAX response.")


@app.get("/")
def read_root():
	return {"message": "Welcome to the McDonald's menu API. Use /all_products/ to get all product names."}


@app.get("/all_products/", response_model=List[Dict[str, Any]])
async def get_all_products():
	load_menu_data()  # Load menu data from file if not loaded
	global menu_items_data
	if menu_items_data:
		return menu_items_data
	
	html = fetch_html(FULL_MENU_URL)
	menu_items = parse_menu(html)
	if menu_items:
		menu_items_data = menu_items  # Store data in the global variable
		save_menu_data()  # Save to JSON file (optional)
		return menu_items_data
	else:
		raise HTTPException(status_code=500, detail="Failed to load menu items from the website.")


@app.get("/products/{product_name}", response_model=Dict[str, Any])
async def get_product(product_name: str):
	load_menu_data()  # Load menu data from file if not loaded
	global menu_items_data
	if not menu_items_data:
		raise HTTPException(status_code=404, detail="Menu data not found.")
	
	# Normalize the product name for comparison
	normalized_product_name = product_name.lower().strip()
	
	for item in menu_items_data:
		if item['name'].lower().strip() == normalized_product_name:
			if 'id' in item:
				product_details = await fetch_product_details_ajax(item['id'])
				
				# Update menu_items_data with product details
				item.update(product_details)
				save_menu_data()  # Save updated data to JSON file
				return item
			else:
				raise HTTPException(status_code=404, detail=f"Product ID not found for '{product_name}'.")
	
	raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")


@app.get("/products/{product_name}/{product_field}", response_model=Any)
async def get_product_field(product_name: str, product_field: str):
	product = await get_product(product_name)
	if product_field in product:
		return product[product_field]
	else:
		raise HTTPException(status_code=404, detail=f"Field '{product_field}' not found for product '{product_name}'.")


if __name__ == '__main__':
	import uvicorn
	
	# Check if the JSON file exists, if not create an empty list
	if not os.path.exists(JSON_FILE_PATH):
		with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
			json.dump([], f)
	
	uvicorn.run(app, host="127.0.0.1", port=8001)
