from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.forms import PostForm, CommentForm
from posts.utils import get_page
from .models import Group, Post, Comment, Follow, User


@cache_page(20, key_prefix="index_page")
def index(request):
    """Функция главной страницы."""
    context = get_page(Post.objects.select_related(
        'group', 'author').all(), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Функция страницы групп."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_page(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Функция страницы пользователя, посты автора."""
    following = ''
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    context = {
        'author': author,
        'following': following,
    }
    context.update(get_page(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Функция страницы отдельного поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related(
        'author').filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция страницы с добавлением нового поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    form.instance.author = request.user
    if form.is_valid():
        form.save()
        return redirect('posts:profile', form.instance.author)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Функция страницы редактирования поста, только для автора."""
    edit_post = get_object_or_404(Post, pk=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post,
    )
    context = {
        'form': form,
        'is_edit': True,
        'edit_post': edit_post,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Лента постов подписок"""
    post = Post.objects.filter(
        author__following__user=request.user
    )
    context = {
        'post': post,
    }
    context.update(get_page(post, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора"""
    user = request.user
    Follow.objects.select_related('user').filter(
        user=user,
        author__username=username).delete()
    return redirect('posts:profile',
                    username=username)
