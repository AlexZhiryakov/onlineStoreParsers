# Для начала, нужно запустить виртуальную среду, в данном случае venv, на windows - venv/Scripts/activate,
# на Linux - source venv/bin/activate
# Пример запуска парсера для Steam: python steam_parser.py --format xlsx --sort inc --filename output.xlsx

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import argparse
import numpy as np
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from converterWB import Сonverter
from selenium.common.exceptions import NoSuchElementException


def priceExtraction(products):
    # Извлекаем цены из списка продуктов
    prices = []
    for item in products:
        price_str = item['price']
        if price_str == "Бесплатно":
            prices.append(0)
        elif price_str == "Цена не найдена":
            continue  # Пропускаем элементы с "Цена не найдена"
        else:
            price_num = price_str.replace(' ', '').replace('руб', '')  # Убираем пробелы и "руб"
            price_num = price_num.replace(',', '.')
            try:
                prices.append(float(price_num))
            except ValueError:
                print(f"Не удалось преобразовать цену: {price_num}")
    return prices

def parse_steam(language):
    url = f'https://store.steampowered.com/search/?sort_by=Released_DESC&filter=popularnew&supportedlang={language}&os=win&ndl=1'
    products = []
    total_count = 0

    # Открывается страница; переход по указанному URL; ожидание, перед появлением элементов на странице
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    driver.get(url)
    wait = WebDriverWait(driver, 50)

    # Ожидание загрузки страницы
    time.sleep(5)  # Ждем загрузки страницы

    # Проверка, прокрутилась ли страница
    last_height = driver.execute_script("return document.body.scrollHeight")
    seen_titles = set()

    # Цикл выполняется, пока количество товаров меньше 250
    while total_count < 250:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Пауза, для загрузки новых элементов после прокрутки
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")

        # Проверка на конец загрузки
        if new_height == last_height:
            break
        last_height = new_height

        # Товары
        items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'search_result_row')))

        # Извлечение данных о каждом товаре
        for item in items:
            try:
                title = item.find_element(By.CLASS_NAME, 'title').text.strip()
                try:
                    price_element = item.find_element(By.CLASS_NAME, 'discount_final_price')
                    price = price_element.text.strip()
                except NoSuchElementException:
                    price = "Цена не найдена"

                # Добавление товара в список
                if title and price and title not in seen_titles:
                    products.append({'title': title, 'price': price})
                    seen_titles.add(title)
                    total_count += 1

                    if total_count >= 250:
                        break

            except Exception as e:
                print(f"Ошибка при извлечении данных: {e}")

        if total_count >= 250:
            break

    driver.quit()

    print(f'Извлеченные продукты: {products}')
    return products, total_count


def save_to_file(products, filename, file_format, sort_order):
    df = pd.DataFrame(products)

    # Определяем порядок сортировки
    ascending_order = (sort_order == 'inc')  # 'inc' - по возрастанию, 'dec' для по убыванию
    df.sort_values(by='title', ascending=ascending_order, inplace=True)

    if file_format == 'csv':
        df.to_csv(filename, index=False)
    elif file_format == 'xlsx':
        df.to_excel(filename, index=False)
    elif file_format == 'json':
        df.to_json(filename, orient='records', lines=True, force_ascii=False)
    else:
        raise ValueError("Unsupported file format. Please use 'csv', 'xlsx', or 'json'.")


def main():
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Парсер для Steam')

    # Аргумент выбора формата сохранения файла (csv, xlsx или json)
    parser.add_argument('--format', choices=['csv', 'xlsx', 'json'], required=True,
                        help='Формат сохранения файла (csv, xlsx или json)')

    # Аргумент выбора порядка сортировки названий товаров (по возрастанию или убыванию)
    parser.add_argument('--sort', choices=['inc', 'dec'], required=True,
                        help='Порядок сортировки названий товаров (inc или dec)')

    # Аргумент названия файла для сохранения данных
    parser.add_argument('--filename', required=True, help='Название файла для сохранения')

    # Сохраняем аргументы командной строки
    args = parser.parse_args()

    langChange = input("Выберите язык игры:\nРусский\nАнглийский\nИспанский\n\nМой выбор: ").lower()

    # Поиск преобразованных значений
    convertedLangChange = None

    # Поиск значения для языка
    for item in Сonverter:
        if langChange in item:
            convertedLangChange = item[langChange]
            break

    # Вызываем функцию для парсинга данных с сайта и получаем выводы
    products, total_count = parse_steam(convertedLangChange)

    print(products)

    # Проверка на пустоту списка
    if not products:
        print("Не удалось собрать данные. Проверьте селекторы или доступность сайта.")
        return

    # Вызов функции для сохранения собранных данных в файл
    save_to_file(products, args.filename, args.format, args.sort)

    prices = priceExtraction(products)

    # Проверяем, есть ли цены для вычисления медианы
    if prices:
        median_price = np.median(prices)
        print(f'Медианная цена товаров: {median_price} ₽')
    else:
        print('Нет доступных цен для вычисления медианы.')

if __name__ == '__main__':
    main()