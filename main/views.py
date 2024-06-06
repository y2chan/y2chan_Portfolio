import os
from django.shortcuts import render
from datetime import datetime, timedelta
from django.utils import timezone
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import logging
from itertools import groupby
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Board, Post
from .forms import PostForm, BoardForm
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.models import User

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == settings.CUSTOM_USERNAME and password == settings.CUSTOM_PASSWORD:
            # 로그인 성공 메시지 및 리디렉션 처리
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            login(request, user)
            return redirect('main:board_list')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('main:board_list')

logger = logging.getLogger(__name__)

# 환경변수 파일 로드
load_dotenv()

BUS_API_KEY = os.getenv('BUS_API_KEY')
SUBWAY_API_KEY = os.getenv('SUBWAY_API_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

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

def home(request):
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

    # 뉴스 API 처리
    if query:
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }
        params = {'query': query, 'display': 3}
        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        for item in result['items']:
            item['title'] = item['title'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['description'] = item['description'].replace('<b>', '<strong>').replace('</b>', '</strong>')
            item['pubDate'] = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y년 %m월 %d일 %H시 %M분')
        context['news'] = result['items']

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

    # 버스 API
    handle_bus_api(context)  # 버스 API 처리를 별도의 함수로 분리 가정

    return render(request, 'home.html', context)

def handle_bus_api(context):
    api_key = BUS_API_KEY
    bus_urls = [
        # 삼육대후문.논골.한화아파트
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=222001597&busRouteId=100100039&ord=16", # 202
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=222001597&busRouteId=100100165&ord=22", # 1155
        # 삼육대앞
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000055&busRouteId=100100039&ord=18", # 202
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000055&busRouteId=100100165&ord=24", # 1155
        # 화랑대역1번출구
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000018&busRouteId=100100039&ord=106", # 202
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000018&busRouteId=100100165&ord=44", # 1155
        # 태릉입구역7번출구.서울생활사박물관
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000017&busRouteId=100100165&ord=42", # 1155
        # 석계역(석계역4번출구)
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=107000057&busRouteId=100100165&ord=40", # 1155
        # 석계역1번출구.A
        f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000183&busRouteId=100100165&ord=38" # 1155
    ]
    grouped_data = {"direction_1": [], "direction_2": []}
    try:
        for api_url in bus_urls:
            response = requests.get(api_url)
            root = ET.fromstring(response.text)
            data = {
                "stNm": root.find(".//stNm").text,
                "rtNm": root.find(".//rtNm").text,
                "arrmsg1": root.find(".//arrmsg1").text,
                "arrmsg2": root.find(".//arrmsg2").text,
            }
            if data["stNm"] in ["삼육대후문.논골.포레나별내", "삼육대앞"]:
                grouped_data["direction_1"].append(data)
            else:
                grouped_data["direction_2"].append(data)
        grouped_data["direction_1"] = group_by_stNm(grouped_data["direction_1"])
        grouped_data["direction_2"] = group_by_stNm(grouped_data["direction_2"])
        context['bus_info'] = grouped_data
    except Exception as e:
        context['bus_info'] = {'error': str(e)}

def group_by_stNm(data):
    # 먼저 데이터를 stNm 기준으로 정렬합니다.
    sorted_data = sorted(data, key=lambda x: x['stNm'])
    # 그룹화된 데이터를 딕셔너리 형태로 변환합니다.
    grouped_data = {}
    for key, group in groupby(sorted_data, key=lambda x: x['stNm']):
        grouped_data[key] = list(group)
    return grouped_data

## 모바일 용 view
from django.views.generic import TemplateView

class mobile_home(TemplateView):
    template_name = 'mobile/m_home.html'

    def get_current_base_datetime(self):
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

    def get(self, request, *args, **kwargs):
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

        # 뉴스 API 처리
        if query:
            headers = {
                'X-Naver-Client-Id': NAVER_CLIENT_ID,
                'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
            }
            params = {'query': query, 'display': 3}
            response = requests.get(url, headers=headers, params=params)
            result = response.json()

            for item in result['items']:
                item['title'] = item['title'].replace('<b>', '<strong>').replace('</b>', '</strong>')
                item['description'] = item['description'].replace('<b>', '<strong>').replace('</b>', '</strong>')
                item['pubDate'] = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y년 %m월 %d일 %H시 %M분')
            context['news'] = result['items']

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

        # 버스 API
        handle_bus_api(context)  # 버스 API 처리를 별도의 함수로 분리 가정

        return render(request, self.template_name, context)

    def handle_bus_api(context):
        api_key = BUS_API_KEY
        bus_urls = [
            # 삼육대후문.논골.한화아파트
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=222001597&busRouteId=100100039&ord=16", # 202
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=222001597&busRouteId=100100165&ord=22", # 1155
            # 삼육대앞
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000055&busRouteId=100100039&ord=18", # 202
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000055&busRouteId=100100165&ord=24", # 1155
            # 화랑대역1번출구
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000018&busRouteId=100100039&ord=106", # 202
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000018&busRouteId=100100165&ord=44", # 1155
            # 태릉입구역7번출구.서울생활사박물관
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000017&busRouteId=100100165&ord=42", # 1155
            # 석계역(석계역4번출구)
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=107000057&busRouteId=100100165&ord=40", # 1155
            # 석계역1번출구.A
            f"http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?serviceKey={api_key}&stId=110000183&busRouteId=100100165&ord=38" # 1155
        ]
        grouped_data = {"direction_1": [], "direction_2": []}
        try:
            for api_url in bus_urls:
                response = requests.get(api_url)
                root = ET.fromstring(response.text)
                data = {
                    "stNm": root.find(".//stNm").text,
                    "rtNm": root.find(".//rtNm").text,
                    "arrmsg1": root.find(".//arrmsg1").text,
                    "arrmsg2": root.find(".//arrmsg2").text,
                }
                if data["stNm"] in ["삼육대후문.논골.포레나별내", "삼육대앞"]:
                    grouped_data["direction_1"].append(data)
                else:
                    grouped_data["direction_2"].append(data)
            grouped_data["direction_1"] = group_by_stNm(grouped_data["direction_1"])
            grouped_data["direction_2"] = group_by_stNm(grouped_data["direction_2"])
            context['bus_info'] = grouped_data
        except Exception as e:
            context['bus_info'] = {'error': str(e)}

    def group_by_stNm(data):
        # 먼저 데이터를 stNm 기준으로 정렬합니다.
        sorted_data = sorted(data, key=lambda x: x['stNm'])
        # 그룹화된 데이터를 딕셔너리 형태로 변환합니다.
        grouped_data = {}
        for key, group in groupby(sorted_data, key=lambda x: x['stNm']):
            grouped_data[key] = list(group)
        return grouped_data

def board_list(request):
    boards = Board.objects.all()
    return render(request, 'blog/board_list.html', {'boards': boards})

def post_list(request, board_slug):
    board = get_object_or_404(Board, slug=board_slug)
    posts = Post.objects.filter(board=board).order_by('-created_at')
    paginator = Paginator(posts, 10)  # 한 페이지당 10개의 게시물
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'blog/post_list.html', {'board': board, 'posts': posts})

def post_detail(request, board_slug, post_slug):
    post = get_object_or_404(Post, board__slug=board_slug, slug=post_slug)
    return render(request, 'blog/post_detail.html', {'post': post})

@login_required
def post_create(request, board_slug):
    board = get_object_or_404(Board, slug=board_slug)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.board = board
            post.save()
            return redirect('main:post_list', board_slug=board.slug)
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form, 'board': board})

@login_required
def post_edit(request, board_slug, post_slug):
    board = get_object_or_404(Board, slug=board_slug)
    post = get_object_or_404(Post, board__slug=board_slug, slug=post_slug)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('main:post_detail', board_slug=board_slug, post_slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_form.html', {'form': form, 'board': board})


@login_required
def post_delete(request, board_slug, post_slug):
    post = get_object_or_404(Post, board__slug=board_slug, slug=post_slug)
    if request.method == 'POST':
        post.delete()
        return redirect('main:post_list', board_slug=board_slug)
    return render(request, 'blog/post_confirm_delete.html', {'post': post})

@login_required
def board_create(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:board_list')
    else:
        form = BoardForm()
    return render(request, 'blog/board_form.html', {'form': form})

@login_required
def board_edit(request, board_slug):
    board = get_object_or_404(Board, slug=board_slug)
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            return redirect('main:board_list')
    else:
        form = BoardForm(instance=board)
    return render(request, 'blog/board_form.html', {'form': form})

@login_required
def board_delete(request, board_slug):
    board = get_object_or_404(Board, slug=board_slug)
    if request.method == 'POST':
        board.delete()
        return redirect('main:board_list')
    return render(request, 'blog/board_confirm_delete.html', {'board': board})