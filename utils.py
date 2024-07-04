import json
import os
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from requests import Response

from consts import GLOBAL_HEADERS, BASE_URL, JSON_FILE_PATH, PRODUCT_BASE_URL


async def fetch_data(url: str) -> Response:
    response = requests.get(url, headers=GLOBAL_HEADERS)
    response.raise_for_status()
    return response


def extract_menu_item(section) -> Optional[Dict[str, Any]]:
    item = {}
    try:
        link = section.find("a", class_="cmp-category__item-link")
        if link and link.has_attr("href"):
            item["link"] = BASE_URL + link["href"]

        name = section.find("div", class_="cmp-category__item-name")
        if name:
            item["name"] = name.text.strip()

        item_id = (
            section["data-product-id"] if "data-product-id" in section.attrs else None
        )
        if item_id:
            item["id"] = item_id
    except Exception as e:
        print(f"Error extracting menu item: {e}")
        return None

    return item


def parse_menu(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    menu_items = {}

    menu_sections = soup.find_all("li", class_="cmp-category__item")
    if not menu_sections:
        raise HTTPException(
            status_code=404, detail="No product cards found on the page."
        )

    for section in menu_sections:
        item = extract_menu_item(section)
        if item:
            menu_items[item["id"]] = item

    return menu_items


async def fetch_product_details_ajax(product_id: str) -> Dict[str, Any]:
    ajax_url = f"{PRODUCT_BASE_URL}{product_id}"
    response = await fetch_data(ajax_url)
    data = response.json()

    if "item" in data and data["item"]:
        item = data["item"]
        product_details = {
            "name": item.get("item_name", "N/A"),
            "description": item.get("description", "N/A"),
            "calories": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Калорійність"
                ),
                "N/A",
            ),
            "fats": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Жири"
                ),
                "N/A",
            ),
            "carbs": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Вуглеводи"
                ),
                "N/A",
            ),
            "proteins": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Білки"
                ),
                "N/A",
            ),
            "unsaturated_fats": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "НЖК"
                ),
                "N/A",
            ),
            "sugar": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Цукор"
                ),
                "N/A",
            ),
            "salt": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Сіль"
                ),
                "N/A",
            ),
            "portion": next(
                (
                    nutrient["value"]
                    for nutrient in item["nutrient_facts"]["nutrient"]
                    if nutrient["name"] == "Вага порції"
                ),
                "N/A",
            ),
            "ingredients": item.get("item_ingredient_statement", "N/A"),
            "allergens": item.get("item_allergen", "N/A"),
        }
        return product_details

    raise HTTPException(
        status_code=404, detail="Product details not found in AJAX response."
    )


async def load_data() -> Dict[str, Any]:
    data = {}
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


async def save_data(product_details: Dict[str, Any]) -> None:
    with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(product_details, f, ensure_ascii=False, indent=4)
