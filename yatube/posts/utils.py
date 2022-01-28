from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def func_paginator(request, post_list):
    """
    Функция вывода пагинации
    """
    paginator = Paginator(post_list, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Если страница не является целым числом, поставим первую страницу
        page_obj = paginator.page(1)
    except EmptyPage:
        # Если страница больше максимальной,
        # подставляем последнюю страницу результатов
        page_obj = paginator.page(paginator.num_pages)
    return page_obj
