import pandas as pd
import numpy as np

import requests
import json
import datetime
import aiohttp

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder

data = pd.read_csv('temperature_data.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    
def analysis(city_name):

    """
    Принимает на вход название города

    Проводит анализ временного ряда температуры для выбранного города и выдает:
      1. mean, min, max температуры за весь период (по нынешнему сезону)
      2. Строит скользящие mean, std
      3. Ищет аномалии на основе (rolling_mean ± sigma * rolling_std)
      4. Составляет сезонный профиль (mean и std по сезонам)
      5. Находит тренд (линейная регрессия): положительный или отрицательный

    """

    data_copy = data.copy()
    # я решил, что нужен текущий сезон - то есть на дату запроса пользователя 
    current_month = datetime.datetime.now().month

    if current_month in [12, 1, 2]:
        current_season = 'winter'
    elif current_month in [3, 4, 5]:
        current_season = 'spring'
    elif current_month in [6, 7, 8]:
        current_season = 'summer'
    else:
        current_season = 'autumn'

    city_season_df = data_copy.loc[
        (data_copy['season'] == current_season) &
        (data_copy['city'] == city_name)
    ].copy()

    min_temp = city_season_df['temperature'].min()
    max_temp = city_season_df['temperature'].max()
    mean_temp = city_season_df['temperature'].mean()

    print(
        f"Текущий сезон для города {city_name}: {current_season}\n\n"
        f"Минимальная температура в сезоне: {min_temp}\n"
        f"Максимальная температура в сезоне: {max_temp}\n"
        f"Средняя температура в сезоне:  {mean_temp}\n"
    )

    city_season_df['rolling_mean'] = city_season_df.groupby(
        'city')['temperature'].rolling(window=30).mean().reset_index(level=0, drop=True)

    city_season_df['rolling_std'] = city_season_df.groupby(
        'city')['temperature'].rolling(window=7).std().reset_index(level=0, drop=True)

    city_season_df['is_anomaly'] = (
        (city_season_df['temperature'] > city_season_df['rolling_mean'] + 2 * city_season_df['rolling_std']) |
        (city_season_df['temperature'] < city_season_df['rolling_mean'] - 2 * city_season_df['rolling_std'])
    )

    # Для изучения тренда

    city_season_df['days_from_start'] = (
        city_season_df['timestamp'] - city_season_df['timestamp'].min()
    ).dt.days

    X = city_season_df[['days_from_start']]
    y = city_season_df['temperature']
    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0]
  
    if slope > 0:
        trend_value = 'Положительный тренд'
    elif slope < 0:
        trend_value = 'Отрицательный тренд'
    else:
        trend_value = 'Нет явного тренда'

    city_season_df['trend'] = trend_value
    city_season_df.drop(columns='days_from_start', inplace=True)
    print(f'Профиль текущего сезона города {city_name}')
    print(city_season_df.tail(5))

def parallel_analysis(cities):
    """
    Параллельный запуск анализа для списка городов
    """
    with Pool() as pool:
        pool.map(analysis, cities)


def current_temp(cityname):
    
    """
    Получает текущую погоду для указанного города через OpenWeatherMap API и 
    сравнивает её с исторической «нормой» на этот же день и месяц 
    (без учёта года и не учитывает непосредственно сезон)

    Порядок действий:
    1. Формирует URL-запрос к OpenWeatherMap, используя API-ключ и название города.
    2. Получает JSON-ответ и извлекает из него текущую температуру (в Кельвинах).
    3. Переводит температуру в градусы Цельсия и выводит оба значения (K и °C).
    4. Определяет дату из ответа (только число и месяц), находит в датафрейме `data` (глобальная переменная)
       соответствующие исторические записи для того же города и дня-месяца, но без аномальных дней.
    5. Расчитывает «верхнюю» и «нижнюю» границы нормы (Mean ± 2 * Std) на основе столбца `rolling_mean` 
       (сглаженное среднее) из `same_day_month_df`.
    6. Сравнивает текущую температуру с вычисленными границами и выводит, выше ли она нормы, ниже нормы 
       или находится в пределах нормы.

    Принимает: название города, для которого нужно получить текущую температуру
        и провести сравнение с историческими данными

    Возвращает: функция выводит результаты и ничего не возвращает

    Основа запроса с API: https://www.geeksforgeeks.org/python-find-current-weather-of-any-city-using-openweathermap-api/

    Докстринг сгенерирован GPT4
    """
 
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
  
    complete_url = base_url + "appid=" + api_key + "&q=" + cityname
 
    response = requests.get(complete_url)
    x = response.json()

    raw_dt = x['dt']
    converted_dt = datetime.datetime.utcfromtimestamp(raw_dt)  
    converted_date_str = converted_dt.strftime('%Y-%m-%d')

    same_day_month_df = data[
        (data['timestamp'].dt.day == converted_dt.day) &
        (data['timestamp'].dt.month == converted_dt.month) &
        (data['city'] == cityname)
    ].copy()


    same_day_month_df['rolling_mean'] = data.groupby('city')['temperature'].rolling(window=30).mean().reset_index(level=0, drop=True)
    same_day_month_df['rolling_std'] = data.groupby('city')['temperature'].rolling(window=7).std().reset_index(level=0, drop=True)

    print(f"Текущая температура: {x['main']['temp']} K / {x['main']['temp'] - 273.15:.2f} °C")
    print(same_day_month_df['rolling_mean'].mean())
    print(same_day_month_df['rolling_mean'].std())

    current_temp_c = x['main']['temp'] - 273.15

    upper_bound = same_day_month_df['rolling_mean'].mean() + 3 * same_day_month_df['rolling_mean'].std()
    lower_bound = same_day_month_df['rolling_mean'].mean() - 3 * same_day_month_df['rolling_mean'].std()

    if current_temp_c > upper_bound:
        print("Текущая погода выше нормы для текущего сезона")
    elif current_temp_c < lower_bound:
        print("Текущая погода ниже нормы для текущего сезона")
    else:
        print("Погода нормальна для текущего сезона")

async def async_current_temp(cityname):
    
    """
    
    Асинхронная версия функции current_temp
    
    """

    api_key = "b7afd6b1373d8c63689dbc1c096c69ae"
 
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
  
    complete_url = base_url + "appid=" + api_key + "&q=" + cityname
 
    async with aiohttp.ClientSession() as session:
        async with session.get(complete_url) as response:
            x = await response.json()

    raw_dt = x['dt']
    converted_dt = datetime.datetime.utcfromtimestamp(raw_dt)  
    converted_date_str = converted_dt.strftime('%Y-%m-%d')

    same_day_month_df = data[
        (data['timestamp'].dt.day == converted_dt.day) &
        (data['timestamp'].dt.month == converted_dt.month) &
        (data['city'] == cityname)
    ].copy()


    same_day_month_df['rolling_mean'] = data.groupby('city')['temperature'].rolling(window=30).mean().reset_index(level=0, drop=True)
    same_day_month_df['rolling_std'] = data.groupby('city')['temperature'].rolling(window=7).std().reset_index(level=0, drop=True)

    print(f"Текущая температура: {x['main']['temp']} K / {x['main']['temp'] - 273.15:.2f} °C")
    print(same_day_month_df['rolling_mean'].mean())
    print(same_day_month_df['rolling_mean'].std())

    current_temp_c = x['main']['temp'] - 273.15

    upper_bound = same_day_month_df['rolling_mean'].mean() + 3 * same_day_month_df['rolling_mean'].std()
    lower_bound = same_day_month_df['rolling_mean'].mean() - 3 * same_day_month_df['rolling_mean'].std()

    if current_temp_c > upper_bound:
        print("Текущая погода выше нормы для текущего сезона")
    elif current_temp_c < lower_bound:
        print("Текущая погода ниже нормы для текущего сезона")
    else:
        print("Погода нормальна для текущего сезона")

async def process_cities(city_list, data):
    """
    Асинхронная обработка списка городов
    """
    tasks = [current_temp(city, data) for city in city_list]
    await asyncio.gather(*tasks)
