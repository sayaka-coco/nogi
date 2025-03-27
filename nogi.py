import streamlit as st
import requests
import urllib.parse
import os
from dotenv import load_dotenv
import datetime
import re
from bs4 import BeautifulSoup
from utils import style_buttons

# 環境変数の読み込み
load_dotenv()

style_buttons()

# 背景色をミントグリーンに設定
st.markdown(
    """
    <style>
        body {
            background-color: #98FF98;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# タイトルを表示
st.markdown("""
    <h1 style='text-align: center; color: #2C2319; font-size:70px; '>NOGI NOG</h1>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    rating_threshold = st.slider("Googleマップ評価", 2.0, 5.0, 3.0, step=0.1)

with col2:
    search_query_1 = st.text_input("エリア・駅（例:銀座、渋谷）", "")

with col3:
    search_query_2 = st.text_input("キーワード（例:焼肉、店名）", "")

st.markdown("<hr>", unsafe_allow_html=True)

def get_instagram_search_url(store_name):
    base_url = "https://www.instagram.com/explore/search/keyword/?q="
    return base_url + urllib.parse.quote(store_name)

def highlight_today_hours(text):
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    today_name = weekdays[datetime.datetime.today().weekday()]
    lines = text.split("\n")
    updated_lines = [
        line.replace(today_name, f"<b>{today_name}</b>") if today_name in line else line
        for line in lines
    ]
    return "<br>".join(updated_lines)

def get_tabelog_info(store_name):
    """食べログの店舗情報をスクレイピング"""
    search_url = f"https://tabelog.com/search/?SrtT=rt&sw={urllib.parse.quote(store_name)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
    }
    try:
        search_response = requests.get(search_url, headers=headers)
        if search_response.status_code == 200:
            search_soup = BeautifulSoup(search_response.content, 'html.parser')
            link_tag = search_soup.find("a", class_="list-rst__rst-name-target")
            if link_tag:
                store_url = link_tag.get("href")
                store_response = requests.get(store_url, headers=headers)
                if store_response.status_code == 200:
                    store_soup = BeautifulSoup(store_response.content, 'html.parser')
                    rating_tag = store_soup.find("b", class_="c-rating__val")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "評価なし"
                    return store_url, rating
    except Exception as e:
        return "取得失敗", "取得失敗"
    return "見つかりませんでした", "見つかりませんでした"

api_key = os.getenv("API_KEY")
url = "https://places.googleapis.com/v1/places:searchText"
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.currentOpeningHours,places.reviews,places.googleMapsLinks,places.rating"
}

if st.button("🔍 検索", key="search_button", help="店舗情報を検索"):
    params = {"textQuery": f"{search_query_1} AND {search_query_2}", "languageCode": "ja"}
    response = requests.post(url, headers=headers, json=params)

    if response.status_code == 200:
        places = response.json().get("places", [])
        filtered_places = []
        for place in places:
            name = place.get("displayName", {}).get("text", "名前なし")
            rating = place.get("rating", 0.0)
            google_maps_link = place.get("googleMapsLinks", {}).get("placeUri", "リンクなし")
            opening_hours = highlight_today_hours("\n".join(
                place.get("currentOpeningHours", {}).get("weekdayDescriptions", ["営業時間情報なし"])
            ))
            instagram_url = get_instagram_search_url(name)
            tabelog_url, tabelog_rating = get_tabelog_info(name)

            if rating >= rating_threshold:
                filtered_places.append({
                    "name": name,
                    "rating": rating,
                    "tabelog_rating": tabelog_rating,
                    "google_maps_link": google_maps_link,
                    "instagram_url": instagram_url,
                    "opening_hours": opening_hours,
                    "tabelog_url": tabelog_url
                })

        if filtered_places:
            for place in filtered_places:
                with st.container():
                    st.markdown(f"""
                        <div style='padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #F6FAF5;'>
                            <h3 style='color: #2C2319;'>{place['name']}</h3>
                            <p><b>⭐ Googleマップ評価:</b> {place['rating']}</p>
                            <p><b>🍽️ 食べログ評価:</b> {place['tabelog_rating']}</p>
                            <p><a href='{place['google_maps_link']}' target='_blank'>📍 Googleマップで見る</a></p>
                            <p><a href='{place['instagram_url']}' target='_blank'>📷 Instagramで検索</a></p>
                            <p><a href='{place['tabelog_url']}' target='_blank'>🔗 食べログページ</a></p>
                            <p><b>🕒 営業時間:</b><br>{place['opening_hours']}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("該当する店舗が見つかりませんでした。")
    else:
        st.error(f"APIリクエストに失敗しました: {response.status_code}")
        st.write(response.text)
