import base64
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

class SimpleBasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 인증이 필요한 경로 설정
        protected_paths = [
            '/blog/board/new/',
            '/blog/board/<slug:board_slug>/edit/',
            '/blog/board/<slug:board_slug>/delete/',
            '/blog/board/<slug:board_slug>/post/new/',
            '/blog/board/<slug:board_slug>/post/<slug:post_slug>/edit/',
            '/blog/board/<slug:board_slug>/post/<slug:post_slug>/delete/',
        ]

        # 현재 요청 경로가 보호된 경로 중 하나인지 확인
        if any(request.path.startswith(path.replace('<slug:board_slug>', '').replace('<slug:post_slug>', '')) for path in protected_paths):
            if not request.user.is_authenticated:
                if not self._perform_basic_auth(request):
                    return HttpResponse('Unauthorized', status=401)

        return self.get_response(request)

    def _perform_basic_auth(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            auth_method, auth = auth_header.split(' ', 1)
            if auth_method.lower() == 'basic':
                username, password = base64.b64decode(auth.strip()).decode('utf-8').split(':', 1)
                if self._check_credentials(username, password):
                    user = authenticate(request, username=username, password=password)
                    if user:
                        login(request, user)
                        return True
        return False

    def _check_credentials(self, username, password):
        return username == settings.CUSTOM_USERNAME and password == settings.CUSTOM_PASSWORD
