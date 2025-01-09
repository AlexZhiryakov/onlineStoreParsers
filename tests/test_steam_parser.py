from steam_parser import priceExtraction

def test_priceExtraction():
    products = [
        {'title': 'My Summer Car', 'price': '286 руб'},
        {'title': 'Chocolate Factory Simulator', 'price': '586,80 руб'},
        {'title': 'Screen Cat', 'price': '37 руб'},
        {'title': 'Only Up: ВОСХОЖДЕНИЕ РУСОВ', 'price': '160 руб'},
        {'title': 'Тварюк', 'price': '140 руб'},
        {'title': 'Royal Quest Online', 'price': 'Бесплатно'},
    ]

    # Ожидаемый результат
    expected_prices = [
        286.0, 586.80, 37.0, 160.0, 140.0, 0.0
    ]

    # Проверяем результат работы функции
    result = priceExtraction(products)
    assert result == expected_prices, f"Expected {expected_prices}, but got {result}"