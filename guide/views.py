from django.shortcuts import render
from django.http import JsonResponse
import json
from guide.word_analysis import *
from pprint import pprint
import re

def wrap_each_word_in_span(text, verse_data, verse_number):
    words = text.split(" ")

    result = f'<span class="verse-number">{verse_number}</span>'

    for word in words:
        strong_num = ""
        word_info = get_word_info_from_verse(verse_data, word)
        if word_info:
            strong_num = word_info["strong_num"]

        span = f'<span class="verse-word" strongnum="{strong_num}">{word}</span>'
        result += span

    return result


def guide_page(request, book, chapter, *args, **kwargs):

    bible_gateway_text = get_esv_text_biblegateway(book, chapter)

    verses_text = re.sub(r"\[\w\]", "", bible_gateway_text) # get rid of [a], [k] etc.
    verses = verses_text.split("\n")

    verses_content = ""

    chapter_info = get_chapter_bible_hub(book_name=book, chapter_num=chapter)

    for index, v in enumerate(verses):
        verse_num = index + 1
        verse_num_text = f"verse{verse_num}"

        verse_words_wrapped = wrap_each_word_in_span(v, chapter_info[str(verse_num)], verse_num)

        verse_span = f'<span class="verse" id="{verse_num_text}">{verse_words_wrapped}</span>'
        verses_content += verse_span

    return render(request, "guide/guide_page.html", context={
        "verses_content": verses_content,
        "chapter_info": chapter_info,
        "book": book,
        "chapter": chapter
    })

def get_chapter_info(request, *args, **kwargs):
     if request.method == "POST":
        data = json.loads(request.body)
        book = get_cleaned_alpha_text(data.get("book"))
        chapter = data.get("chapter")

        chapter_info = get_chapter_bible_hub(book_name=book, chapter_num=chapter)
        return JsonResponse(chapter_info)

def get_word_info_from_verse(verse_info, word):
    cleaned_word = get_cleaned_alpha_text(word)
    candidates = []
    candidate_numbers = []

    for word_info in verse_info:
        if cleaned_word in word_info["english"]:
            candidates.append(word_info)
            candidate_numbers.append(word_info["strong_num"])

    if len(set(candidate_numbers)) == 0:
        # try again with 'ing', 'er' etc. removed and see if there is exactly one result
        
        word_ends = [
            "ing",
            "er",
            "ed",
            "s",
            "e",
            "an",
            "y"
        ]

        shortened_word = cleaned_word
        shortened_candidates = []

        for we in word_ends:
            shortened_word = shortened_word.removesuffix(we)

        for word_info in verse_info:
            if shortened_word in word_info["english"]:
                shortened_candidates.append(word_info)

        if len(shortened_candidates) == 1:
            return shortened_candidates[0]

        return None

    if len(set(candidate_numbers)) == 1:
        return candidates[0]

    else:
        # look for exact match 
        new_candidates = []

        for c in candidates:
            if cleaned_word == word_info["english"]:
                new_candidates.append(c)

        if len(new_candidates) == 1:
            return new_candidates[0]
        if len(new_candidates) != 0:
            print("multiple candidates")
            print(new_candidates)

def get_word_info(request, *args, **kwargs):
    if request.method == "POST":
        data = json.loads(request.body)
        word = get_cleaned_alpha_text(data.get("word"))
        verse = data.get("verse").replace("verse", "") # ie. verse14

        chapter_info = get_chapter_bible_hub(book_name="john", chapter_num=3)

        verse_info = chapter_info[verse]
        word_info = get_word_info_from_verse(verse_info, word)

        return JsonResponse({"result": "success", "word_info": word_info})
