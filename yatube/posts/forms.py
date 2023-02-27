from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для создания/редактирования поста."""

    class Meta:
        model = Post
        fields = ("text", "group", "image")


class CommentForm(forms.ModelForm):
    """Форма добавления комментария."""

    class Meta:
        model = Comment
        fields = ("text",)
