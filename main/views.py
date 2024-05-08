import os
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
import requests
import json
import datetime

BUS_API_KEY = os.getenv('BUS_API_KEY')
SUBWAY_API_KEY = os.getenv('SUBWAY_API_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
Naver_Client_Id = os.getenv('Naver_Client_Id')
Naver_Client_Secret = os.getenv('Naver_Client_Secret')

def home(request):
    # 네이버 검색 API를 호출할 URL을 설정합니다.
    url = "https://openapi.naver.com/v1/search/news.json"

    # URL 파라미터에서 검색어를 가져옵니다. 기본값은 빈 문자열입니다.
    query = request.GET.get('query', '')

    if query:
        # API를 호출할 때 사용할 파라미터를 설정합니다.
        params = {'query': query, 'display': 20}

        # API를 호출할 때 사용할 헤더를 설정합니다. 클라이언트 ID와 시크릿은 실제 값으로 변경해야 합니다.
        headers = {
            'X-Naver-Client-Id': Naver_Client_Id,
            'X-Naver-Client-Secret': Naver_Client_Secret
        }

        # API를 호출하고 응답을 가져옵니다.
        response = requests.get(url, headers=headers, params=params)

        # 응답을 JSON 형식으로 파싱합니다.
        result = json.loads(response.text)

        for item in result['items']:
            item['title'] = item['title'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['description'] = item['description'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['pubDate'] = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y년 %m월 %d일 %H시 %M분')

        # 결과와 검색어를 템플릿에 전달합니다.
        return render(request, 'home.html', {'news': result['items'], 'query': query})

    else:  # 검색어가 없는 경우 빈 결과를 전달합니다.
        return render(request, 'home.html', {'news': [], 'query': query})