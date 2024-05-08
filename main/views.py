import os
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
import requests
import json
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# 환경변수 파일 로드
load_dotenv()

BUS_API_KEY = os.getenv('BUS_API_KEY')
SUBWAY_API_KEY = os.getenv('SUBWAY_API_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def home(request):
    return render(request, 'home.html')

def syugpt(request):
    return render(request, "syugpt.html")

def get_current_base_datetime():
    now = timezone.now()
    current_hour = now.hour
    base_time = None

    if current_hour < 2.5:
        base_time = '2300'
        base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
    elif current_hour < 5.5:
        base_time = '0200'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 8.5:
        base_time = '0500'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 11.5:
        base_time = '0800'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 14.5:
        base_time = '1100'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 17.5:
        base_time = '1400'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 20.5:
        base_time = '1700'
        base_date = now.strftime('%Y%m%d')
    elif current_hour < 23.5:
        base_time = '2000'
        base_date = now.strftime('%Y%m%d')
    else:
        base_time = '2300'
        base_date = now.strftime('%Y%m%d')

    return base_date, base_time

def get_weather(city):
    api_key = BUS_API_KEY
    base_date, base_time = get_current_base_datetime()
    url = f'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey={api_key}&numOfRows=10&pageNo=1&base_date={base_date}&base_time={base_time}&nx=62&ny=128&dataType=JSON'
    response = requests.get(url, timeout=10)

    try:
        data = response.json()

        if 'response' not in data or 'body' not in data['response'] or 'items' not in data['response']['body']:
            raise ValueError("Invalid API response format")

        # 데이터 추출 및 처리
        temperature = None
        weather_status = None
        wind_speed = None
        precipitation_type = None

        for item in data['response']['body']['items']['item']:
            category = item['category']
            fcst_value = item['fcstValue']

            if category == 'TMP':
                temperature = fcst_value
            elif category == 'SKY':
                fcst_value = int(fcst_value)
                if 0 <= fcst_value <= 5:
                    weather_status = '구름 없음'
                elif 6 <= fcst_value <= 8:
                    weather_status = '구름 많음'
                elif 9 <= fcst_value <= 10:
                    weather_status = '흐림'
            elif category == 'WSD':
                fcst_value = float(fcst_value)
                if 0 <= fcst_value < 4:
                    wind_speed = '선선함'
                elif 4 <= fcst_value < 9:
                    wind_speed = '약풍'
                elif 9 <= fcst_value < 14:
                    wind_speed = '강풍'
                elif 14 <= fcst_value:
                    wind_speed = '심한 강풍'
            elif category == 'PTY':
                fcst_value = int(fcst_value)
                if fcst_value == 0:
                    precipitation_type = '맑음'
                elif fcst_value == 1:
                    precipitation_type = '비'
                elif fcst_value == 2:
                    precipitation_type = '비/눈'
                elif fcst_value == 3:
                    precipitation_type = '눈'
                elif fcst_value == 4:
                    precipitation_type = '소나기'

        # 현재 날짜 및 시간 설정
        today_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')

        # 결과 데이터를 딕셔너리로 저장
        weather_info = {
            'today_date': today_date,
            'current_time': current_time,
            'temperature': temperature if temperature is not None else 'N/A',
            'weather_status': weather_status if weather_status is not None else 'N/A',
            'wind_speed': wind_speed if wind_speed is not None else 'N/A',
            'precipitation_type': precipitation_type if precipitation_type is not None else 'N/A',
        }

    except ValueError as e:
        weather_info = {
            'today_date': 'N/A',
            'current_time': 'N/A',
            'temperature': 'N/A',
            'weather_status': 'N/A',
            'wind_speed': 'N/A',
            'precipitation_type': 'N/A',
        }

    return weather_info

def gabean(request):
    url = "https://openapi.naver.com/v1/search/news.json"
    query = request.GET.get('query', '')
    subway_name = request.GET.get('subway_name', '')
    city = "서울특별시 노원구 화랑로 815"
    context = {'query': query, 'city': city}

    # 날씨 API
    try:
        weather_info = get_weather(city)
    except requests.Timeout:
        weather_info = {
            'today_date': 'N/A',
            'current_time': 'N/A',
            'temperature': 'N/A',
            'weather_status': 'N/A',
            'wind_speed': 'N/A',
            'precipitation_type': '서버 응답 시간 초과',
        }
    context['weather_info'] = weather_info

    # 뉴스 API
    if query:
        params = {'query': query, 'display': 3}
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }

        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        for item in result['items']:
            item['title'] = item['title'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['description'] = item['description'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['pubDate'] = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y년 %m월 %d일 %H시 %M분')
        context['news'] = result['items']
    else:
        context['news'] = []

    # 지하철 API
    if subway_name:
        api_key = SUBWAY_API_KEY
        api_url = f"http://swopenapi.seoul.go.kr/api/subway/{api_key}/xml/realtimeStationArrival/0/5/{subway_name}"
        response = requests.get(api_url)
        root = ET.fromstring(response.text)
        grouped_data = {}

        for element in root.findall(".//row"):
            statnNm = element.find(".//statnNm").text
            if statnNm not in grouped_data:
                grouped_data[statnNm] = []

            if len(grouped_data[statnNm]) < 2:  # 최대 2개의 정보만 저장
                data = {
                    "statnNm": statnNm,
                    "trainLineNm": element.find(".//trainLineNm").text,
                    "arvlMsg2": element.find(".//arvlMsg2").text,
                    "recptnDt": element.find(".//recptnDt").text,
                }
                grouped_data[statnNm].append(data)

        context['subway_info'] = grouped_data


    return render(request, 'gabean.html', context)
