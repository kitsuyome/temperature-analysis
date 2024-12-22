import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime
from io import StringIO

st.title("Анализ температур")

st.sidebar.header("Загрузка данных")
uploaded_file = st.sidebar.file_uploader("Загрузите файл с историческими данными (CSV)", type="csv")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    st.sidebar.success("Файл успешно загружен!")
else:
    st.sidebar.warning("Загрузите файл, чтобы продолжить.")
    st.stop()

st.sidebar.header("Настройки API")
api_key = st.sidebar.text_input("Введите API-ключ OpenWeatherMap", type="password")

cities = data['city'].unique()

st.sidebar.header("Выбор города")
selected_city = st.sidebar.selectbox("Выберите город", cities)

st.header(f"Анализ температур для города: {selected_city}")
city_data = data[data['city'] == selected_city]

st.subheader("Описательная статистика")
st.write(city_data[['temperature']].describe())

st.subheader("Временной ряд температур")
time_series_fig = px.line(city_data, x='timestamp', y='temperature', title=f"Температура в городе {selected_city}")
st.plotly_chart(time_series_fig)

st.subheader("Сезонные профили")
city_data['season'] = city_data['timestamp'].dt.month % 12 // 3 + 1
seasonal_profile = city_data.groupby('season')['temperature'].agg(['mean', 'std']).reset_index()
seasonal_profile['season'] = seasonal_profile['season'].replace({1: 'Winter', 2: 'Spring', 3: 'Summer', 4: 'Autumn'})
seasonal_fig = px.bar(seasonal_profile, x='season', y='mean', error_y='std', title="Сезонный профиль температуры")
st.plotly_chart(seasonal_fig)

st.subheader("Аномалии температуры")
city_data['rolling_mean'] = city_data['temperature'].rolling(window=30).mean()
city_data['rolling_std'] = city_data['temperature'].rolling(window=30).std()
city_data['is_anomaly'] = (
    (city_data['temperature'] > city_data['rolling_mean'] + 2 * city_data['rolling_std']) |
    (city_data['temperature'] < city_data['rolling_mean'] - 2 * city_data['rolling_std'])
)
anomalies_fig = px.scatter(
    city_data, x='timestamp', y='temperature', color='is_anomaly',
    title="Аномалии температуры"
)
st.plotly_chart(anomalies_fig)

if api_key:
    st.subheader("Текущая температура")
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={api_key}&q={selected_city}"
    response = requests.get(complete_url)

    if response.status_code == 200:
        weather_data = response.json()
        current_temp_k = weather_data['main']['temp']
        current_temp_c = current_temp_k - 273.15

        st.metric("Текущая температура (°C)", f"{current_temp_c:.2f}")
        mean_temp = city_data['temperature'].mean()
        std_temp = city_data['temperature'].std()
        lower_bound = mean_temp - 2 * std_temp
        upper_bound = mean_temp + 2 * std_temp

        if current_temp_c < lower_bound:
            st.warning("Температура ниже нормы!")
        elif current_temp_c > upper_bound:
            st.warning("Температура выше нормы!")
        else:
            st.success("Температура в пределах нормы.")
    elif response.status_code == 401:
        st.error("Некорректный API-ключ.")
    else:
        st.error(f"Ошибка API: {response.status_code}")
