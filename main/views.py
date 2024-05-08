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

# 환경변수 파일 로드
load_dotenv()

BUS_API_KEY = os.getenv('BUS_API_KEY')
SUBWAY_API_KEY = os.getenv('SUBWAY_API_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def home(request):
    url = "https://openapi.naver.com/v1/search/news.json"
    query = request.GET.get('query', '')

    if query:
        params = {'query': query, 'display': 3}
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }

        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        # 뉴스 데이터를 처리
        for item in result['items']:
            item['title'] = item['title'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['description'] = item['description'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['pubDate'] = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y년 %m월 %d일 %H시 %M분')

        return render(request, 'home.html', {'news': result['items'], 'query': query})
    else:
        return render(request, 'home.html', {'news': [], 'query': query})