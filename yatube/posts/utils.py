from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, post_list, post_num=settings.POSTS_NUM):
    # нужно очищать кэш при смене страницы - ??!!
    my_paginator = Paginator(post_list, post_num)
    page_number = request.GET.get('page')
    page_obj = my_paginator.get_page(page_number)
    return page_obj
