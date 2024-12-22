import time
import asyncio
import aiohttp
import pandas as pd

from scripts import current_temp, async_current_temp, analysis
from multiprocessing import Pool

data = pd.read_csv('temperature_data.csv')
cities = data['city'].unique()

def test_sync_analysis():
    """Тест синхронного анализа"""
    start_time = time.time()
    for city in cities:
        analysis(city)
    end_time = time.time()
    avg_time = (end_time - start_time) / len(cities)
    print(f"Среднее время выполнения синхронного анализа на один город: {avg_time:.2f} секунд")
    print(f"Общее время выполнения синхронного анализа: {end_time - start_time:.2f} секунд")

def test_parallel_analysis():
    """Тест параллельного анализа"""
    start_time = time.time()
    with Pool() as pool:
        pool.map(analysis, cities)
    end_time = time.time()
    avg_time = (end_time - start_time) / len(cities)
    print(f"Среднее время выполнения параллельного анализа на один город: {avg_time:.2f} секунд")
    print(f"Общее время выполнения параллельного анализа: {end_time - start_time:.2f} секунд")

def test_sync_temp():
    """Тест синхронной функции"""
    start_time = time.time()
    total_time = 0
    for city in cities:
        city_start = time.time()
        current_temp(city)
        city_end = time.time()
        total_time += (city_end - city_start)
    end_time = time.time()
    avg_time = total_time / len(cities)
    print(f"Среднее время выполнения синхронно на один город: {avg_time:.2f} секунд")
    print(f"Общее время выполнения синхронно: {end_time - start_time:.2f} секунд")

async def test_async_temp():
    """Тест асинхронной функции"""
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities:
            city_start = time.time()
            tasks.append(async_current_temp(city))
            city_end = time.time()
        await asyncio.gather(*tasks)
    end_time = time.time()
    avg_time = (end_time - start_time) / len(cities)
    print(f"Среднее время выполнения асинхронно на один город: {avg_time:.2f} секунд")
    print(f"Общее время выполнения асинхронно: {end_time - start_time:.2f} секунд")
