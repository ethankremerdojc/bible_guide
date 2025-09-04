from django.shortcuts import render, redirect
from bible_guide.settings import BIBLE_VERSIONS, BIBLE_BOOKS
from django.http import JsonResponse
import json
from pprint import pprint
import re
from django.middleware.csrf import get_token
from guide.word_analysis import *

def gen_one_redirect(request):
    return redirect("guide_page", book="genesis", chapter="1")

def guide_page(request, book, chapter, *args, **kwargs):
    return render(request, "guide/guide_page.html", context={
        "book": book,
        "chapter": chapter,
        "bibleversions": BIBLE_VERSIONS,
        "biblebooks": [b[0] for b in BIBLE_BOOKS],
        "biblechaptercounts": [b[1] for b in BIBLE_BOOKS],
        "csrftoken": get_token(request)
    })

def get_chapter_info(request, *args, **kwargs):
    data = json.loads(request.body)
    book = get_cleaned_alpha_text(data.get("book"))
    chapter = data.get("chapter")
    version = data.get("version")

    chapter_info = get_chapter_bible_hub(book_name=book, chapter_num=chapter)
    chapter_html = get_chapter_html(book=book, chapter=chapter, version=version, chapter_info=chapter_info)

    return JsonResponse({"chapterInfo": chapter_info, "chapterText": chapter_html})

def get_word_info(request, *args, **kwargs):
    data = json.loads(request.body)
    word = get_cleaned_alpha_text(data.get("word"))
    verse = data.get("verse").replace("verse", "") # ie. verse14

    chapter_info = get_chapter_bible_hub(book_name="john", chapter_num=3)

    verse_info = chapter_info[verse]
    word_info = get_word_info_from_verse(verse_info, word)

    return JsonResponse({"result": "success", "word_info": word_info})
