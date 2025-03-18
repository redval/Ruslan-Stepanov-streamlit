import numpy as np
import pandas as pd
import streamlit as st
import requests
import matplotlib.pyplot as plt


def get_current_temperature(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"

    response = requests.get(url)

    data = response.json()

    if response.status_code == 200:
        return data["main"]["temp"]
    else:
        return response.json()


def get_season_temperature(df, city, season):
    historical_temperature = df.groupby(["city", "season"]).get_group((city, season))["temperature"]
    return historical_temperature


def is_anomaly(df, city, season):
    season_temperature = get_season_temperature(df, city, season)

    mean = np.mean(season_temperature)
    std = np.std(season_temperature)

    lower_bound = mean - std
    upper_bound = mean + std

    city_current_temperature = get_current_temperature(city, api_key)

    is_anomaly = ((city_current_temperature < lower_bound) | (city_current_temperature > upper_bound))

    result = "Да" if is_anomaly else "Нет"

    return f"Является ли аномалией нынешняя температура в городе {city}?\nОтвет: {result}"


def show_statistic_information(df, selected_city, year):
    df_city = df[df["city"] == selected_city]

    min_temperature = df_city["temperature"].min()
    max_temperature = df_city["temperature"].max()

    min_temperature_date = df_city[df_city["temperature"] == min_temperature]["timestamp"].values[0]
    max_temperature_date = df_city[df_city["temperature"] == max_temperature]["timestamp"].values[0]

    mean_temperature_spring = df_city[df_city["season"] == "spring"]["temperature"].mean()

    count_days_with_temperature_above_zero = len(df_city[(df_city["temperature"] < 0) & (df["timestamp"].str.contains(year))])
    count_days_with_temperature_below_zero = len(df_city[(df_city["temperature"] > 0) & (df["timestamp"].str.contains(year))])

    st.markdown(f"Минимальная температура: {min_temperature}°C (дата: {min_temperature_date})")
    st.markdown(f"Максимальная температура: {max_temperature}°C (дата: {max_temperature_date})")

    st.markdown(f"Средняя температура весной: {mean_temperature_spring}°C")

    st.markdown(f"Количество дней с температурой выше нуля за {year} год: {count_days_with_temperature_above_zero}")
    st.markdown(f"Количество дней с температурой ниже нуля за {year} год: {count_days_with_temperature_below_zero}")


def show_temperature_plot(df, city, season, year):
    df_city_season = df[(df["city"] == city) & (df["season"] == season) & (df["timestamp"].str.contains(year))]

    season_temperature = get_season_temperature(df, city, season)

    mean = np.mean(season_temperature)
    std = np.std(season_temperature)

    lower_bound = mean - std
    upper_bound = mean + std

    plt.figure(figsize=(20, 5))

    plt.plot(df_city_season["timestamp"], df_city_season["temperature"], label="Температура")

    plt.axhline(y=mean, color="b", linestyle="--", label="Среднее")
    plt.axhline(y=lower_bound, color="r", linestyle="-", label="Верхнее отклонение")
    plt.axhline(y=upper_bound, color="r", linestyle="-", label="Нижнее отклонение")

    plt.fill_between(df_city_season["timestamp"], mean - std, mean + std, color="green", alpha=0.3)

    plt.title(f"Временной ряд температуры в городе {city} за сезон {season} {year} года")

    plt.xlabel("Дата")
    plt.ylabel("Температура")

    plt.legend()
    plt.grid()

    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=20))

    st.pyplot(plt)

def show_season_profiles(df, city):
    df_city = df[df["city"] == city]

    seasonal_profiles = df_city.groupby(["season"]).agg({'temperature': [np.mean, np.std]})
    seasonal_profiles.columns = ["Средняя температура", "Стандартное отклонение"]
    st.write(seasonal_profiles)


# Код самого приложения
st.title("Температура в разных городах")

file = st.file_uploader("Выберите CSV-файл", type="csv")

if file is not None:
    df = pd.read_csv(file)
    st.write(df)

    cities = list(df["city"].unique())

    selected_city = st.selectbox('Выберите город:', cities)
    current_season = "spring"
    year = "2019"

    st.write(f'Вы выбрали: {selected_city}')

    api_key = st.text_input("Введите ключ API-ключ OpenWeatherMap")

    if st.button("Отправить"):
        current_temperature = get_current_temperature(selected_city, api_key)
        if type(current_temperature) is float:
            st.markdown(f"Сейчас температура в городе {selected_city} равна {current_temperature}.")
            st.markdown(is_anomaly(df, selected_city, current_season))
            show_statistic_information(df, selected_city, year)
            show_temperature_plot(df, selected_city, current_season, year)
            show_season_profiles(df, selected_city)
        else:
            st.markdown(current_temperature)
