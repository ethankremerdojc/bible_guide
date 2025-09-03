"""
URL configuration for bible_guide project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from guide.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('guide/<str:book>/<str:chapter>/', guide_page, name="guide_page"),
    path('get_word_info/', get_word_info, name="get_word_info"),
    path('get_chapter_info/', get_chapter_info, name="get_chapter_info")
]
