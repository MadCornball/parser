# McDonald's Menu API

This project is a FastAPI application that collects and retrieves information about McDonald's products from the official website. The data is saved locally in JSON format.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/parser.git
    cd parser
    ```

2. Ensure you have Python 3.7 or higher installed. Install the necessary dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Running the Application

1. Start the FastAPI application:
    ```sh
    uvicorn main:app --reload
    ```

2. The application will be available at: `http://127.0.0.1:8000`

## Usage

### Get All Products

To get a list of all products, navigate to:
    http://127.0.0.1:8000/all_products/


This endpoint will load HTML content from the McDonald's website, extract product information, and save it to the `menu_data.json` file.

### Get Product Information

To get information about a specific product, navigate to:
    http://127.0.0.1:8000/products/{product_name}

    Replace `{product_name}` with the name of the product. For example:
        http://127.0.0.1:8000/products/Big%20Mac

