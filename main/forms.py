from django import forms
from .models import Post, Board

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['name', 'description']
