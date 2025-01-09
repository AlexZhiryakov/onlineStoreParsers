# Для начала, нужно запустить виртуальную среду, в данном случае venv, на windows - venv/Scripts/activate,
# на Linux - source venv/bin/activate
# Пример запуска парсера для WB: python wildberries_parser.py --format xlsx --sort inc --filename output.xlsx

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
import re
from converterWB import Сonverter


def clean_title(title):
    # Убираем лишние символы
    title = title.replace('"', '')  # Убираем кавычки
    title = title.replace('/', '')   # Убираем слеши
    title = re.sub(r's+', ' ', title)  # Убираем лишние пробелы
    title = title.strip()  # Убираем пробелы в начале и конце
    return title

def parse_wildberries(convertedSexChange, convertedCatalogChange):
    url = f'https://www.wildberries.ru/catalog/{convertedSexChange}/odezhda/{convertedCatalogChange}'
    products = []
    total_count = 0 # Счетчик количества товаров

    # Открывается страница; переход по указанному URL; ожидание, перед появлением элементов на странице
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get(url)
    wait = WebDriverWait(driver, 50)

    # Ожидание загрузки страницы
    time.sleep(5)

    # Получаем количество страниц
    pagination = driver.find_elements(By.CLASS_NAME, 'pagination-item')
    total_pages = int(pagination[-1].text) if pagination else 1

    # Цикл проходит по всем страницам
    for page in range(1, total_pages + 1):
        if page > 1:
            driver.get(f"{url}?page={page}")
            time.sleep(5)  # Увеличиваем время ожидания

        # Прокручиваем страницу вниз для загрузки товаров
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Ждем загрузки новых товаров

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Изменяем селектор для получения карточек товара
        items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'product-card')))

        # Извлечение названия и цены из каждого товара
        for item in items:
            try:
                quantity = driver.find_element(By.CLASS_NAME, 'goods-count').text.strip()
                title = item.find_element(By.CLASS_NAME, 'product-card__name').text.strip()
                price = item.find_element(By.CLASS_NAME, 'price__lower-price').text.strip().replace('₽', '').replace(
                    ' ', '')

                # Очищаем название товара
                cleaned_title = clean_title(title)

                if cleaned_title and price:
                    products.append({'title': cleaned_title, 'price': float(price)})
                    total_count += 1
            except Exception as e:
                print(f"Ошибка при извлечении данных: {e}")

        # Если количество товаров уже более 300 то цикл прерывается
        if total_count >= 300:
            break

    # Закрывает браузер и выводит нужные данные
    driver.quit()
    return products, total_count, quantity


def save_to_file(products, filename, file_format, sort_order):
    df = pd.DataFrame(products)

    # Определяем порядок сортировки
    ascending_order = (sort_order == 'inc')  # 'inc' - по возрастанию, 'dec' - по убыванию
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
    parser = argparse.ArgumentParser(description='Парсер для Wildberries')

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

    sexChange = input("Выберите пол для товара:\nЖенщинам\nМужчинам\n\nМой выбор: ").lower()

    if sexChange == 'женщинам':
        catalogChange = input("Выберите категорию товара:\nБлузки и рубашки\nБрюки\nВерхняя одежда\nДжемперы, водолазки и кардиганы\nКомбинезоны\nКостюмы\nФутболки и топы\nЮбки\n\nМой выбор: ").lower()
    elif sexChange == 'мужчинам':
        catalogChange = input("Выберите категорию товара:\nБрюки\nВерхняя одежда\nДжемперы, водолазки и кардиганы\nДжинсы\nКостюмы\n\nМой выбор: ").lower()
    else:
        print("Введите пожалуйста корректный текст")

    convertedSexChange = None
    convertedCatalogChange = None

    # Поиск значения для категории
    for item in Сonverter:
        if catalogChange in item:
            convertedCatalogChange = item[catalogChange]
            break

    if not convertedCatalogChange:
        print("Введите пожалуйста корректный текст")
        return

    # Поиск значения для пола
    for item in Сonverter:
        if sexChange in item:
            convertedSexChange = item[sexChange]
            break

    # Вызываем функцию для парсинга данных с сайта и получаем выводы
    products, total_count, quantity = parse_wildberries(convertedSexChange, convertedCatalogChange)

    print(products)

    # Проверка на пустоту списка
    if not products:
        print("Не удалось собрать данные. Проверьте селекторы или доступность сайта.")
        return

    # Вызов функции для сохранения собранных данных в файл
    save_to_file(products, args.filename, args.format, args.sort)

    # Извлекаем цены из списка продуктов
    prices = [product['price'] for product in products]

    # Находим медианную цену товаров
    median_price = np.median(prices)

    print(f'Из {quantity} мы проанализировали {total_count} товаров и выяснили, что медианная цена товаров: {median_price} ₽')


if __name__ == '__main__':
    main()