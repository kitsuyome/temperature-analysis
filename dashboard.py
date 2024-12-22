import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime
from io import StringIO
from streamlit_option_menu import option_menu

if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

with st.sidebar:
    selected = option_menu(
        "Навигация",
        ["Главная", "Анализ", "Сравнение", "Куда вам слетать отдохнуть?"],
        icons=["house", "bar-chart", "columns", "airplane"],
        menu_icon="menu-app",
        default_index=0
    )

if selected == "Главная":
    st.title("Добро пожаловать в Анализ температур")
    st.write(
        "Этот дашборд позволяет анализировать исторические данные о температуре, "
        "выявлять аномалии, а также получать текущие данные через API OpenWeatherMap."
    )

    st.session_state['uploaded_file'] = st.file_uploader("Загрузите файл с историческими данными (CSV)", type="csv")
    st.session_state['api_key'] = st.text_input("Введите API-ключ OpenWeatherMap", type="password")

    if st.session_state['uploaded_file'] is None or not st.session_state['api_key']:
        st.warning("Пожалуйста, загрузите CSV файл и введите API-ключ, чтобы продолжить.")
        st.stop()
    else:
        st.session_state['data'] = pd.read_csv(st.session_state['uploaded_file'])
        st.session_state['data']['timestamp'] = pd.to_datetime(st.session_state['data']['timestamp'], errors='coerce')
        st.success("Данные успешно загружены!")

if selected == "Анализ":
    st.title("Анализ температур")

    if st.session_state['data'] is None:
        st.warning("Нет данных для анализа. Перейдите на страницу 'Главная' для загрузки файла.")
        st.stop()

    data = st.session_state['data']
    cities = data['city'].unique()
    selected_city = st.sidebar.selectbox("Выберите город", cities)
    st.header(f"Анализ температур для города: {selected_city}")
    city_data = data[data['city'] == selected_city]

    # Tabs
    tab1, tab2 = st.tabs(["Обзор", "Графики"])

    with tab1:
        st.subheader("Общая информация")
        st.markdown(
            f"- **Максимальная температура**: {city_data['temperature'].max():.2f} °C\n"
            f"- **Минимальная температура**: {city_data['temperature'].min():.2f} °C\n"
            f"- **Средняя температура**: {city_data['temperature'].mean():.2f} °C"
        )

        selected_season = st.selectbox("Выберите сезон", ["Winter", "Spring", "Summer", "Autumn"])
        season_mapping = {"Winter": 1, "Spring": 2, "Summer": 3, "Autumn": 4}
        season_data = city_data[city_data['timestamp'].dt.month % 12 // 3 + 1 == season_mapping[selected_season]]
        if not season_data.empty:
            st.markdown(
                f"- **Максимальная температура в сезоне {selected_season}**: {season_data['temperature'].max():.2f} °C\n"
                f"- **Минимальная температура в сезоне {selected_season}**: {season_data['temperature'].min():.2f} °C\n"
                f"- **Средняя температура в сезоне {selected_season}**: {season_data['temperature'].mean():.2f} °C"
            )
        else:
            st.warning("Нет данных для выбранного сезона.")

        st.subheader("Текущая температура")
        if st.session_state['api_key']:
            base_url = "http://api.openweathermap.org/data/2.5/weather?"
            complete_url = f"{base_url}appid={st.session_state['api_key']}&q={selected_city}"
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

    with tab2:
        st.subheader("Временной ряд температур")
        time_series_fig = px.line(city_data, x='timestamp', y='temperature', title=f"Температура в городе {selected_city}")
        st.plotly_chart(time_series_fig)

        st.subheader("Сезонные профили")
        city_data['season'] = city_data['timestamp'].dt.month % 12 // 3 + 1
        seasonal_profile = city_data.groupby('season')['temperature'].agg(['mean', 'std', 'max', 'min']).reset_index()
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

        st.subheader("Гистограмма температур")
        histogram_fig = px.histogram(city_data, x='temperature', nbins=30, title="Гистограмма температуры")
        st.plotly_chart(histogram_fig)

        st.subheader("Разброс температур")
        scatter_fig = px.scatter(city_data, x='timestamp', y='temperature', title="Разброс температуры")
        st.plotly_chart(scatter_fig)

        st.subheader("Плотность температур")
        density_fig = px.density_heatmap(city_data, x='timestamp', y='temperature', title="Плотность температуры")
        st.plotly_chart(density_fig)

        st.subheader("Средняя температура по дням")
        city_data['day'] = city_data['timestamp'].dt.date
        daily_avg = city_data.groupby('day')['temperature'].mean().reset_index()
        daily_avg_fig = px.line(daily_avg, x='day', y='temperature', title="Средняя температура по дням")
        st.plotly_chart(daily_avg_fig)

if selected == "Сравнение":
    st.title("Сравнение городов")

    if st.session_state['data'] is None:
        st.warning("Нет данных для анализа. Перейдите на страницу 'Главная' для загрузки файла.")
        st.stop()

    data = st.session_state['data']
    selected_cities = st.sidebar.multiselect("Выберите города для сравнения", data['city'].unique(), default=data['city'].unique()[:2])
    comparison_data = data[data['city'].isin(selected_cities)]

    st.subheader("Температурные временные ряды")
    comparison_fig = px.line(comparison_data, x='timestamp', y='temperature', color='city', title="Сравнение температур")
    st.plotly_chart(comparison_fig)

    st.subheader("Средние температуры")
    mean_temps = comparison_data.groupby('city')['temperature'].mean().reset_index()
    mean_fig = px.bar(mean_temps, x='city', y='temperature', title="Средние температуры по городам")
    st.plotly_chart(mean_fig)

    st.subheader("Аномалии по городам")
    comparison_data['rolling_mean'] = comparison_data.groupby('city')['temperature'].transform(lambda x: x.rolling(30).mean())
    comparison_data['rolling_std'] = comparison_data.groupby('city')['temperature'].transform(lambda x: x.rolling(30).std())
    comparison_data['is_anomaly'] = (
        (comparison_data['temperature'] > comparison_data['rolling_mean'] + 2 * comparison_data['rolling_std']) |
        (comparison_data['temperature'] < comparison_data['rolling_mean'] - 2 * comparison_data['rolling_std'])
    )
    comparison_anomalies_fig = px.scatter(
        comparison_data, x='timestamp', y='temperature', color='is_anomaly', symbol='city',
        title="Аномалии температур по городам"
    )
    st.plotly_chart(comparison_anomalies_fig)

if selected == "Куда вам слетать отдохнуть?":
    st.title("Куда вам слетать отдохнуть?")

    if st.session_state['data'] is None:
        st.warning("Нет данных для анализа. Перейдите на страницу 'Главная' для загрузки файла.")
        st.stop()

    data = st.session_state['data']
    st.subheader("Выбор параметров")
    desired_season = st.selectbox("Выберите сезон", ["Winter", "Spring", "Summer", "Autumn"])
    desired_temp = st.slider("Желаемая температура (°C)", min_value=-30, max_value=50, value=(20, 30))

    season_mapping = {"Winter": 1, "Spring": 2, "Summer": 3, "Autumn": 4}
    filtered_data = data.copy()
    filtered_data['season'] = filtered_data['timestamp'].dt.month % 12 // 3 + 1
    filtered_data = filtered_data[filtered_data['season'] == season_mapping[desired_season]]
    filtered_data = filtered_data[(filtered_data['temperature'] >= desired_temp[0]) & (filtered_data['temperature'] <= desired_temp[1])]

    if not filtered_data.empty:
        suggested_city = filtered_data['city'].value_counts().idxmax()
        st.success(f"Рекомендуемый город: {suggested_city}")

        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}appid={st.session_state['api_key']}&q={suggested_city}"
        response = requests.get(complete_url)

        if response.status_code == 200:
            weather_data = response.json()
            current_temp_k = weather_data['main']['temp']
            current_temp_c = current_temp_k - 273.15

            st.metric(f"Текущая температура в {suggested_city} (°C)", f"{current_temp_c:.2f}")
        else:
            st.error(f"Ошибка API: {response.status_code}")
    else:
        st.warning("Не найдено городов, соответствующих вашим критериям.")