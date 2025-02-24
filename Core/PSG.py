import requests
from bs4 import BeautifulSoup
import math
import time

# Список игр
games = [
    "A Demon's Game - Episode 1",
    "A Game of Changes",
    "Abyss Raiders: Uncharted",
    "Akin",
    "Alien Hostage"
]


# Функция для получения ID игры из Steam API
def get_steam_appid(game_name, max_retries=3):
    # URL для получения списка всех приложений из Steam
    app_list_url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"

    for attempt in range(max_retries):
        try:
            # Отправляем запрос на получение списка всех приложений
            response = requests.get(app_list_url)
            if response.status_code != 200:
                print(f"Попытка {attempt + 1}: ошибка при запросе списка приложений Steam.")
                time.sleep(2)  # Ждём перед следующей попыткой
                continue

            # Преобразуем ответ в JSON формат
            data = response.json()
            apps = data.get("applist", {}).get("apps", [])

            # Ищем игру по названию в списке всех приложений
            for app in apps:
                if app["name"].lower() == game_name.lower():
                    return app["appid"]

            # print(f"Попытка {attempt + 1}: ID для игры '{game_name}' не найден.")
        except Exception as e:
            print(f"Попытка {attempt + 1}: ошибка - {e}")

        time.sleep(2)  # Ждём перед следующей попыткой

    print(f"Не удалось найти ID для игры '{game_name}' после {max_retries} попыток.")
    return None


# Функция для получения цены карточек для игры
def get_card_price(game_name, total_min_price, total_avg_price):
    # Получаем ID игры с помощью функции get_steam_appid
    appid = get_steam_appid(game_name)
    if not appid:
        return 0, 0, total_min_price, total_avg_price  # Возвращаем 0, если ID игры не найден

    # Формируем URL для получения данных с сайта SteamCardExchange
    search_url = f"https://www.steamcardexchange.net/index.php?gamepage-appid-{appid}"
    print(f"Запрашиваем URL для '{game_name}': {search_url}\n")

    # Отправляем запрос на сайт SteamCardExchange
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Ошибка при запросе страницы для {game_name}")
        return 0, 0, total_min_price, total_avg_price

    # Парсим HTML-страницу с помощью BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Нахождение количества карточек в игре
    cards_text = soup.get_text()
    index_cards = cards_text.find("Cards")
    if index_cards != -1:
        Number_Of_Cards = cards_text[index_cards + 7]  # 7 - длина "Cards: "

        # Вычисляем половину количества карточек, округленную в большую сторону
        half_count = math.ceil(int(Number_Of_Cards) / 2)

        print(f"Карточек в игре '{game_name}' -", Number_Of_Cards + ".", "Выпадет карточек -", half_count, "\n")
    else:
        print(
            "В данной игре отсутствуют коллекционные карточки или она отсутствует на https://www.steamcardexchange.net/")
        return None, None, total_min_price, total_avg_price
    # Ищем все элементы с классом btn-primary, содержащие цены
    card_elements = soup.find_all('a', class_='btn-primary')

    # Считаем цену
    total_price = 0
    card_count = 0  # Переменная для отслеживания количества найденных карточек
    card_prices = []  # Список для хранения всех найденных цен

    for element in card_elements:
        # Извлекаем цену и преобразуем в float
        try:
            price_text = element.text.strip().replace("Price: $", "")
            price = float(price_text)
            card_prices.append(price)  # Добавляем цену в список
            card_count += 1  # Увеличиваем счетчик карточек

            # Если найдены все карточки, завершаем цикл
            if card_count >= int(Number_Of_Cards):
                break
        except ValueError:
            continue  # Пропускаем некорректные значения

    # Суммируем только первую половину (округленную вверх) карточек
    card_prices.sort()
    total_price = sum(card_prices[:half_count])

    # Усредненная сумма (Типо для большого кол-ва акков более норм число)
    avg_total_price = round(sum(card_prices) / int(Number_Of_Cards) * half_count, 3)

    # Общие данные
    total_min_price += total_price
    total_avg_price += avg_total_price

    return total_price, avg_total_price, total_min_price, total_avg_price


# Основная часть программы: перебор игр и вывод информации
total_min_price = 0
total_avg_price = 0
for game in games:
    print("\n" + "=" * 40)  # Разделитель перед выводом
    # Получаем общую стоимость карточек для игры
    total_price, avg_total_price, total_min_price, total_avg_price = get_card_price(game, total_min_price,
                                                                                    total_avg_price)

    # Выводим результат
    if total_price != 0:
        print(f"Минимальная сумма цен карточек для {game}: ${total_price:.2f}")
        print("")
        print(f"Средняя сумма цен карточек для {game}: ${avg_total_price:.3f}")

    print("=" * 40)  # Разделитель после вывода

# Вывод общих данных
print("")
print(f"Общая минимальная сумма цен карточек: ${total_min_price:.2f}")
print("")
print(f"Общая средняя сумма цен карточек: ${total_avg_price:.3f}")