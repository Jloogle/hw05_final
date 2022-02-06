from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.conf import settings

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import func_paginator


class PostHome(ListView):
    paginate_by = settings.POST_PER_PAGE
    model = Post
    template_name = 'posts/index.html'

    def get_queryset(self):
        return Post.objects.select_related('author').all()


class GroupPosts(ListView):
    paginate_by = settings.POST_PER_PAGE
    model = Post
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        return Post.objects.filter(group__slug=self.kwargs['slug'])

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, slug=self.kwargs['slug'])
        return context


def profile(request, username: str):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    page_obj = func_paginator(request, post_list)
    count = post_list.count()
    count_follower = author.following.count()
    user = request.user
    following = (
        user.is_authenticated
        and author.following.filter(user=user).exists() and (user != author)
    )
    context = {
        'page_obj': page_obj,
        'count': count,
        'author': author,
        'following': following,
        'count_follower': count_follower,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post)
    comments_count = comments.count()
    form = CommentForm()
    context = {
        'comments_count': comments_count,
        'comments': comments,
        'post': post,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    is_edit = False
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, template, context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    user_following = Follow.objects.filter(user=user).values('author')
    post_list = Post.objects.filter(author__in=user_following)
    page_obj = func_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    user = request.user
    author = get_object_or_404(User, username=username)
    if author == user:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=user, author=author)
    return redirect(
        'posts:profile',
        username=username
    )


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    follower.delete()
    return redirect('posts:profile', username=username)
