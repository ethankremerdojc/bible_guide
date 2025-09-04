from django.shortcuts import render, redirect

from django.http import JsonResponse
import json
from guide.word_analysis import *
from pprint import pprint
import re
from django.middleware.csrf import get_token


def gen_one_redirect(request):
    return redirect("guide_page", book="genesis", chapter="1")

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


BIBLE_VERSIONS = [
    "ESV",
    "NIV",
    "NKJV",
    "KJV",
    "NASB",
    "NASV",
    "NLT",
    "CSB",
    "ASV"
]

BIBLE_BOOKS = [
    ("Genesis", 50),
    ("Exodus", 40),
    ("Leviticus", 27),
    ("Numbers", 36),
    ("Deuteronomy", 34),
    ("Joshua", 24),
    ("Judges", 21),
    ("Ruth", 4),
    ("1 Samuel", 31),
    ("2 Samuel", 24),
    ("1 Kings", 22),
    ("2 Kings", 25),
    ("1 Chronicles", 29),
    ("2 Chronicles", 36),
    ("Ezra", 10), 
    ("Nehemiah", 13),
    ("Esther", 10),
    ("Job", 42),
    ("Psalms", 150),
    ("Proverbs", 31),
    ("Ecclesiastes", 12),
    ("Song of Solomon", 8),
    ("Isaiah", 66),
    ("Jeremiah", 52),
    ("Lamentations", 5),
    ("Ezekiel", 48),
    ("Daniel", 12),
    ("Hosea", 14),
    ("Joel", 3),
    ("Amos", 9),
    ("Obadiah", 1),
    ("Jonah", 4),
    ("Micah", 7),
    ("Nahum", 3),
    ("Habakkuk", 3),
    ("Zephaniah", 3),
    ("Haggai", 2),
    ("Zechariah", 14),
    ("Malachi", 4),
    
    ("Matthew", 28),
    ("Mark", 16),
    ("Luke", 24),
    ("John", 21),
    ("Acts", 28),
    ("Romans", 16),
    ("1 Corinthians", 16),
    ("2 Corinthians", 13),
    ("Galatians", 6),
    ("Ephesians", 6),
    ("Philippians", 4),
    ("Colossians", 4),
    ("1 Thessalonians", 5),
    ("2 Thessalonians", 3),
    ("1 Timothy", 6),
    ("2 Timothy", 4),
    ("Titus", 3),
    ("Philemon", 1),
    ("Hebrews", 13),
    ("James", 5),
    ("1 Peter", 5),
    ("2 Peter", 3),
    ("1 John", 5),
    ("2 John", 1),
    ("3 John", 1),
    ("Jude", 1),
    ("Revelation", 22)
]

def get_chapter_html(book, chapter, version, chapter_info):
    verses, headings = get_text_biblegateway(book, chapter, version)
    verses_content = ""

    for verse_num, verse in verses:

        heading = headings.get(verse_num)
        if heading:
            verses_content += f"<h3>{heading}</h3>"

        verse_num_text = f"verse{verse_num}"

        verse_words_wrapped = wrap_each_word_in_span(verse, chapter_info[str(verse_num)], verse_num)

        verse_span = f'<span class="verse" id="{verse_num_text}">{verse_words_wrapped}</span>'
        verses_content += verse_span

    return verses_content

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
            print(new_candidates)

def get_word_info(request, *args, **kwargs):
    data = json.loads(request.body)
    word = get_cleaned_alpha_text(data.get("word"))
    verse = data.get("verse").replace("verse", "") # ie. verse14

    chapter_info = get_chapter_bible_hub(book_name="john", chapter_num=3)

    verse_info = chapter_info[verse]
    word_info = get_word_info_from_verse(verse_info, word)

    return JsonResponse({"result": "success", "word_info": word_info})
