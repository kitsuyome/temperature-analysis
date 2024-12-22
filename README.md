# Анализ температур с помощью исторических данных, API OpenWeather и Streamlit

## Цель

Этот проект предоставляет удобный инструмент для анализа температурных данных с использованием Streamlit. С помощью приложения пользователь может:

- Загружать и анализировать исторические данные о температуре
- Выбирать город для изучения сезонных профилей, аномалий и трендов
- Сравнивать текущую температуру с историческими нормами, используя API OpenWeatherMap

Проект доступен по ссылке: https://temp-analytics.streamlit.app/

## Структура проекта

### main.ipynb

Демонстрация методов и реализации анализа температур, включая:

- Анализ данных и построение сезонных профилей
- Выявление аномалий температуры
- Сравнение различных функций и методов

### scripts.py

Основные функции для анализа данных и работы с API:

- `analysis`: выполняет сезонный анализ и определяет тренды для указанного города
- `current_temp`: получает текущую температуру из OpenWeatherMap API и сравнивает с историческими данными
- `async_current_temp`: асинхронная версия функции current_temp
  
### utils.py

Вспомогательные функции для тестирования производительности:

- `test_sync_analysis()`: оценивает производительность синхронного анализа
- `test_parallel_analysis`: оценивает производительность анализа с распараллеливанием
- `test_async_temp()`: тестирует асинхронные вызовы API для получения текущей температуры
- `test_sync_temp()`: тестирует синхронные вызовы API для получения текущей температуры

## Установка

Клонируйте репозиторий и установите зависимости:

```
git clone https://github.com/kitsuyome/temperature-analysis
cd temperature-analysis
pip install -r requirements.txt
```
## Использование

1. **Загрузка исторических данных:** Загрузите CSV-файл с данными о температуре.
2. **Выбор города:** Выберите город из загруженного набора данных для анализа.
3. **Сезонные профили:** Исследуйте средние значения и стандартные отклонения температуры по сезонам.
4. **Выявление аномалий:** Найдите и визуализируйте отклонения в температурных данных.
5. **Проверка текущей температуры:** Сравните актуальную температуру с историческими данными с помощью API OpenWeatherMap.

### Пример данных

Ваши данные должны быть в следующем формате:

| city       | timestamp           | temperature | season |
|------------|---------------------|-------------|--------|
| New York   | 2023-01-01 00:00:00 | -3.5        | Winter |
| Los Angeles| 2023-07-01 00:00:00 | 25.0        | Summer |

### Ключ

Для использования и тестирования вам необходим API Key от https://openweathermap.org/api

## Лицензия

Этот проект лицензирован под [MIT License](LICENSE).
