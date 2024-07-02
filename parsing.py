# import json
# import os
# import time
#
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from typing import Dict, Any, List
#
# from selenium.webdriver.common import by
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.wait import WebDriverWait
#
# CHROMEDRIVER_PATH = 'D:\\Chromedriver\\chromedriver.exe'
#
# if not os.path.isfile(CHROMEDRIVER_PATH):
#     raise FileNotFoundError(f"The path to chromedriver is not valid: {CHROMEDRIVER_PATH}")
#
#
# def scrape_menu(url: str) -> List[Dict[str, Any]]:
#     options = Options()
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')
#     options.add_argument('--disable-gpu')
#     options.add_argument('--start-maximized')
#     options.add_argument('--enable-logging')
#     options.add_argument('--auto-open-devtools-for-tabs')
#
#     service = Service(executable_path=CHROMEDRIVER_PATH)
#     driver = webdriver.Chrome(service=service, options=options)
#     driver.get(url)
#
#     menu_items = []
#
#     try:
#         while True:
#             # WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CLASS_NAME, 'cmp-category__item'))
#
#             menu_sections = driver.find_element(By.CLASS_NAME,'cmp-category__item')
#
#             for section in menu_sections:
#                 item = {}
#                 item['name'] = section.find_element_by_class_name('cmp-category__item-name').text.strip()
#                 section.find_element_by_class_name('cmp-category__item-link').click()
#                 time.sleep(1)  # Пауза для загрузки страницы
#
#                 item['url'] = driver.current_url
#                 extended_info = get_extended_info(driver.page_source)
#                 item.update(extended_info)
#
#                 menu_items.append(item)
#
#                 driver.back()  # Возвращаемся на предыдущую страницу
#
#             next_button = driver.find_element(By.CLASS_NAME,'.cmp-pagination__button--next')
#             if next_button:
#                 next_button.click()
#                 time.sleep(3)  # Пауза для загрузки следующей страницы
#             else:
#                 break
#
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         driver.quit()
#
#     return menu_items
#
#
# def get_extended_info(page_source: str) -> Dict[str, Any]:
#     item = {}
#     soup = BeautifulSoup(page_source, 'html.parser')
#
#     nutrition_info = soup.find('div', class_='cmp-nutrition-summary')
#     if nutrition_info:
#         item['nutrition'] = {}
#         for nutrition_item in nutrition_info.find_all('li', class_='cmp-nutrition-summary__heading-primary-item'):
#             label = nutrition_item.find('span', class_='metric').text.strip()
#             value = nutrition_item.find('span', class_='value').text.strip()
#             item['nutrition'][label] = value
#
#     return item
#
#
# if __name__ == '__main__':
#     url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
#     menu_items = scrape_menu(url)
#
#     with open('menu_items.json', 'w', encoding='utf-8') as f:
#         json.dump(menu_items, f, ensure_ascii=False, indent=4)
#
#     print(menu_items)
