from core.utils import paginate
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix="index_page")
def index(request):
    """Главная страница."""

    posts = Post.objects.select_related("author", "group")
    page_obj = paginate(request, posts)
    context = {
        "title": "Последние обновления на сайте",
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """Страница постов одной группы."""

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    page_obj = paginate(request, posts)
    context = {
        "title": f'Записи сообщества "{group}"',
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    """Страница профайла пользователя."""

    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("group")
    page_obj = paginate(request, post_list)
    user = request.user
    following = user.is_authenticated and author.following.exists()
    context = {
        "page_obj": page_obj,
        "author": author,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    """Страница поста."""

    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related("author")
    form = CommentForm(request.POST or None)
    context = {
        "title": f"Пост {post}",
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    """Страница добавления нового поста."""

    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", username=post.author)
    context = {
        "title": "Новый пост",
        "button": "Добавить",
        "form": form,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста."""

    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    context = {
        "form": form,
        "title": "Редактировать запись",
        "button": "Сохранить",
    }
    if not form.is_valid():
        return render(request, "posts/create_post.html", context)
    form.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(pk=post_id)
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    """Страница постов на подписанных авторов."""

    user = request.user
    posts_list = Post.objects.filter(author__following__user=user)
    page_obj = paginate(request, posts_list)
    context = {
        "title": "Избранные авторы",
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""

    author = User.objects.get(username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""

    Follow.objects.get(user=request.user, author__username=username).delete()
    return redirect("posts:profile", username=username)
