from django.forms import ModelForm
from django import forms

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 50, 'rows': 10})
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
