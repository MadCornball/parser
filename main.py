from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

from consts import FULL_MENU_URL
from utils import (
    save_data,
    load_data,
    fetch_product_details_ajax,
    fetch_data,
    parse_menu,
)

app = FastAPI()

# Global variable to store menu items data
menu_items_data = {}


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the McDonald's menu API. Use /all_products/ to get all product names."
    }


@app.get("/products/", response_model=List[Dict[str, Any]])
async def get_all_products():
    global menu_items_data  # Use the global variable
    if menu_items_data:
        return menu_items_data.values()

    data = await fetch_data(FULL_MENU_URL)
    menu_items = parse_menu(data.text)
    if menu_items:
        menu_items_data = menu_items  # Store data in the global variable

        # Save to JSON file (optional)
        await save_data(menu_items_data)

        return menu_items_data.values()
    else:
        raise HTTPException(
            status_code=500, detail="Failed to load menu items from the website."
        )


@app.get("/products/{product_name}/", response_model=Dict[str, Any])
async def get_product(product_name: str):
    global menu_items_data
    if not menu_items_data:
        menu_items_data = await load_data()

    normalized_product_name = product_name.lower().strip()
    print(normalized_product_name)
    for item in menu_items_data.values():
        if item["name"].lower().strip() == normalized_product_name:
            if "id" in item:
                product_details_list: dict = await load_data()
                product_details_list[item["id"]] = await fetch_product_details_ajax(
                    item["id"]
                )
                await save_data(product_details_list)

                return product_details_list[item["id"]]
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product ID not found for '{product_name}'.",
                )

    raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")


@app.get("/products/{product_name}/{product_field}/", response_model=Any)
async def get_product_field(product_name: str, product_field: str):
    product = await get_product(product_name)
    if product_field in product:
        return product[product_field]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{product_field}' not found for product '{product_name}'.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
