from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count

# Create your views here.


# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 5)  # по 3 статьи на каждой странице
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # "Если страница не является целым числом возвращаем первую страницу"
        posts = paginator.page(1)
    except EmptyPage:
        # Если номер страницы больше чем общее колличество страниц возвращаем последнюю
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,
                             publish__month=month, publish__day=day)
    # Список активных комментариев для этой статьи.
    comments = post.comments.filter(active=True)
    new_comment = False
    if request.method == 'POST':
        # Пользователь отправил комментарий
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Создаем комментарий но не сохраняем его в БД
            new_comment = comment_form.save(commit=False)
            # Привязываем комментарий к текущей статье.
            new_comment.post = post
            # Сохраняем коментарий в БД
            new_comment.save()
    else:
        comment_form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {'post': post,
                                                     'comments': comments,
                                                     'new_comment': new_comment,
                                                     'comment_form': comment_form,
                                                     'similar_posts': similar_posts
                                                     })




def post_share(request, post_id):
   # Получение статьи по идентификатору
   post = get_object_or_404(Post, pk=post_id, status='published')
   #print(post_id, '+++++++++++++++++++++')
   sent = False
   if request.method == 'POST':
       #print('POST', 'OK+++++++++++++++')
       # форма была отправлена на сохранение
       form = EmailPostForm(request.POST)
       if form.is_valid():
           # все поля формы прошли валидацию
           cd = form.cleaned_data

           # отправка сообщения
           post_url = request.build_absolute_uri(post.get_absolute_url())
           subject = '{}({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
           message = 'Read "{}" at {} \n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
           send_mail(subject, message, 'mishchurmi@yandex.ru', [cd['to']])
           sent = True
       return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent, 'post_id': post_id})
   else:
       form = EmailPostForm(request.POST)
       return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent, 'post_id': post_id})
