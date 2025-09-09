import requests
import json
from bs4 import BeautifulSoup, NavigableString
from pprint import pprint
import re
from tqdm import tqdm
from bible_guide.settings import BIBLE_BOOKS, OT_MAPPING_PKL_PATH, OT_STRONG_PKL_PATH, NT_MAPPING_PKL_PATH, NT_STRONG_PKL_PATH
import pickle

def get_cleaned_alpha_text(text):
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
    return "".join(t for t in text.lower() if t in allowed_chars)

def get_text_biblegateway(book, chapter, version):
    url = f"https://www.biblegateway.com/passage/?search={book.replace(" ", "+")}%20{chapter}&version={version}"
    response = requests.get(url)
    response.encoding = "utf-8"
    response_text = response.text.replace("—", " ")

    soup = BeautifulSoup(response_text, "html.parser")
    chapter_contents = soup.find('div', class_="result-text-style-normal")

    text_blocks = chapter_contents.select('p .text, h3')

    verses = {
        "1": ""
    }

    headings = {}

    verse_number = "1"

    for block in text_blocks:

        if block.name == "h3":
            headings[verse_number] = block.get_text()
            continue

        for child in block:
            if isinstance(child, NavigableString):
                verses[verse_number] += str(child).strip() + " "
                continue
            
            if "versenum" in child.get("class", []):
                verse_number = child.get_text().replace("&nbsp;", "").replace("\xa0", "")
                verses[verse_number] = ""
                continue

            for subchild in child:

                ignore_classes = [
                    "crossreference",
                    "footnote",
                    "chapternum"
                ]
                
                do_skip = False
                for ic in ignore_classes:
                    if ic in subchild.parent.get("class", []):
                        do_skip = True
                if do_skip:
                    continue
                
                if isinstance(subchild, NavigableString):
                    verses[verse_number] += str(subchild).strip() + " "
                    continue

                if "versenum" in subchild.get("class", []):
                    verse_number = subchild.get_text().replace("&nbsp;", "").replace("\xa0", "")
                    verses[verse_number] = ""

            #elif (child.name == "span" and "woj" in child.get("class", [])) or (child.name == "span" and "text" in child.get("class", [])):
            #    child_text_nodes = child.find_all(string=True, recursive=False)
            #    parts.append("".join(child_text_nodes).strip())

        #verses[verse_number] += joined_parts + "\n"

    tup_version = sorted([(vnum, re.sub(r"\[\w\]", "", verse)) for vnum, verse in verses.items()], key=lambda x: int(x[0]))
    #result = ""
    #for t in tup_version:
    #    if headings.get(t[0]):
    #        result += f"|{headings.get(t[0])}|"
    #    result += t[1] + "\n"
    #result = result[:-1]

    return tup_version, headings

def get_chapter_bible_hub(response_html):
    # if this gets ip banned, (like home network) we can make the request from the users browser, then 
    ## send that to the backend with the initial post request
    #url = f"https://biblehub.com/interlinear/{book_name.replace(' ', '_')}/{chapter_num}.htm"
    #response = requests.get(url)
    #response.encoding = "utf-8"
    #response_html = response.text

    soup = BeautifulSoup(response_html, "html.parser")
    chapter_contents = soup.select(".chap")[0]

    verses = []
    current_verse = None

    language = "greek"
    posname = "pos"
    refname = "refmain"

    contents = chapter_contents.select(".tablefloat td")
    if not contents: # hopefully this is hebrew
        contents = chapter_contents.select('.tablefloatheb td[valign="middle"]')
        language = "hebrew"
        posname = "strongs"
        refname = "refheb"

    for table_data in contents:
        if not table_data.get_text().strip():
            continue
        
        strongs_title_pattern = r'<[^<]*title="([^>]*)>'

        strong_num = table_data.find("span", class_=posname).get_text()

        try:
            strong_a_tag = table_data.find("span", class_=posname).find("a")

            if len(strong_a_tag.attrs.keys()) == 2: # should only have href and title, if more than something went wrong on their end
                strong_text = re.search(strongs_title_pattern, str(strong_a_tag)).group(1)
            else:
                # something like this:
                #<a href="/greek/4639.htm" title="Strong\'s Greek 4639: Apparently a primary word; " shade"="" or="" a="" shadow="" (darkness="" of="" error="" an="" adumbration)."="">4639</a>
                # find original html, bs4 gonna screw everything up
                a_tag = re.search(f'<a[^>]*>{strong_num}</a>', response_html).group()
                strong_text = re.search(f'title="(.*)">', a_tag).group(1)

        except AttributeError: # weird punctuation
            continue
        original_language = table_data.find("span", class_=language).get_text() #TODO need to select other languages
        english_literal = table_data.find("span", class_="eng").get_text()

        word_info = {
            "strong_num": strong_num,
            "strong_text": strong_text[strong_text.index(":") + 2:], # everything after : in Strongs Greek 1234: ...
            "original_language": original_language,
            "language_type": language,
            "english": get_cleaned_alpha_text(english_literal.replace("\xa0", " "))
        }
        
        try:
            verse_num = table_data.find("span", class_=refname).get_text().replace("\xa0", "")
            
            if current_verse is not None:
                verses.append(current_verse)

            current_verse = {
                "num": verse_num,
                "words": []
            }
        except AttributeError as e:
            pass
        
        already_in_verse = False
        for w in current_verse["words"]:
            if w["strong_num"] == strong_num:
                already_in_verse = True
        if not already_in_verse:
            current_verse["words"].append(word_info)

    verses.append(current_verse)

    result = {}

    for v in verses:
        result[v["num"]] = v["words"]

    return result

def get_bible_book_index(book_name):
    lowercase_books = [ b[0].lower() for b in BIBLE_BOOKS ]
    return lowercase_books.index(book_name) + 1

#    with open(NT_MAPPING_PKL_PATH, 'rb') as ntmf:
#        NT_MAPPING = pickle.load(ntmf)
#    with open(NT_STRONG_PKL_PATH, 'rb') as ntdf:
#        NT_STRONG_DATA = pickle.load(ntdf)

"""
word_info = {
    "strong_num": strong_num,
    "strong_text": strong_text[strong_text.index(":") + 2:], # everything after : in Strongs Greek 1234: ...
    "original_language": original_language,
    "language_type": language,
    "english": get_cleaned_alpha_text(english_literal.replace("\xa0", " "))
}
"""

def get_ot_strongs_text(data):
    strong_data = data['strongs']

    if strong_data.get('meaning'):
        if strong_data['meaning'].get('def'):
            meaning_def = strong_data['meaning']['def']
        else:
            meaning_def = ""

        if strong_data['meaning'].get("#text"):
            meaning = strong_data['meaning']['#text']
        else:
            meaning = ""
    else:
        meaning_def = ""
        meaning = ""

    if strong_data.get('usage'):
        usage = strong_data.get('usage')
    else:
        usage = ""

    strong_text = strong_data.get('#text', "") 

    bdb_data = data['bdb']
    if bdb_data:
        bdb_text = bdb_data['#text']
    else:
        bdb_text = ""

    return f'{meaning_def}: {meaning} | {usage} | {strong_text} BDB: {bdb_text}'


def get_formatted_ot_data(data):
    strong_num = data["strongs"]["@id"]

    bdb_text = None
    if data['bdb']:
        bdb_text = data['bdb']['#text']
   
    description = get_ot_strongs_text(data)

    strong_usage = data['strongs']['usage']
    if type(strong_usage) == str:
        strong_usage = [strong_usage]
    
    if type(strong_usage) == dict:
        if type(strong_usage['w']) == list:
            strong_usage = [strong_usage['w'][0]['#text']]
        else:
            strong_usage = [strong_usage['w']['#text']]

    ref_strong_usage = []
    if data["strongs"].get('reference_words'):
        ref_strong_usage = data["strongs"]["reference_words"][0]["usage"]
   
        if type(strong_usage) == str:
            strong_usage = [strong_usage]
 
        if type(ref_strong_usage) == dict:
            if type(ref_strong_usage['w']) == list:
                ref_strong_usage = [ref_strong_usage['w'][0]['#text']]
            else:
                ref_strong_usage = [ref_strong_usage['w']['#text']]
    # format later

    original_language = data['strongs']['w']['#text']
    language_type = "hebrew"

    if not data['strongs'].get('meaning'):
        english = data['strongs']['reference_words'][0]['meaning']['def']
    else:
        english = data['strongs']['meaning']['def']

    if type(english) == str:
        english = [english]

    return {
        "strong_num": strong_num,
        "description": description,
        "bdb_text": bdb_text,
        "original_language": original_language,
        "language_type": language_type,
        "english": english,
        "strongs_options": data['strongs_options'],
        "strongs_usage": strong_usage,
        "ref_strongs_usage": ref_strong_usage,
        "bdb_options": data['bdb_options'],

        # turn this on for debuggingb
        #"old_strong_data": data['strongs'],
    }

def get_ot_chapter_data(book_index, chapter):
    with open(OT_MAPPING_PKL_PATH, 'rb') as otmf:
        OT_MAPPING = pickle.load(otmf)
    with open(OT_STRONG_PKL_PATH, 'rb') as otdf:
        OT_STRONG_DATA = pickle.load(otdf)

    book_mapping = OT_MAPPING[str(book_index)]
    chapter_mapping = book_mapping[chapter]

    result = {}

    for verse_number, verse_data in chapter_mapping.items():
        verse_result = []
        strongs_nums = verse_data['strongs']
        
        for strong_num in strongs_nums:
            #try:
            ot_data = OT_STRONG_DATA.get(strong_num)
            if not ot_data:
                continue
            verse_result.append(get_formatted_ot_data(ot_data))
            #except KeyError:
            #    continunpute

        result[verse_number] = verse_result
    return result

def get_nt_chapter_data(book_index, chapter):
    pass

def get_chapter_data(book, chapter):
    bible_book_index = get_bible_book_index(book)

    if bible_book_index < 40:
        return get_ot_chapter_data(bible_book_index, chapter)
    else:
        return get_nt_chapter_data(bible_book_index, chapter)

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

def get_candidates(items, word, key, exact_match=True):
    candidates = []

    for item in items:

        item_data = item[key]
        if type(item_data) != list:
            item_data = [item_data]

        for english_option in item_data:
            cleaned = get_cleaned_alpha_text(english_option)
            if exact_match == True:
                if word == cleaned:
                    candidates.append(item)
                    break
            else:
                if word in cleaned:
                    candidates.append(item)
                    break

    return candidates

def get_candidates_shortened(items, word, key, exact_match):
    word_ends = [
        "ment",
        "ites",
        "ing",
        "er",
        "ed",
        "an",
        "ful",
        "lty",
        "less",
        "ly",
        "e",
        "s",
        "y"
    ]

    shortened_candidates = []

    for word_end in word_ends:
        shortened_word = word.removesuffix(word_end)
        candidates = get_candidates(items, shortened_word, key, exact_match)
        shortened_candidates = shortened_candidates + candidates

    return shortened_candidates

def get_word_info_with_retry_exact(verse_info, word, key):
    word_info = get_word_info(verse_info, word, key, exact_match=True)

    if not word_info:
        return get_word_info(verse_info, word, key, exact_match=False)

    return word_info

def get_word_info(verse_info, word, key, exact_match=True):
    candidates = get_candidates(verse_info, word, key, exact_match=exact_match)

    if len(candidates) == 1:
        return candidates

    elif len(candidates) == 0:
        shortened_candidates = get_candidates_shortened(verse_info, word, key, exact_match=exact_match)

        if len(shortened_candidates) == 1:
            return shortened_candidates
    
        if len(shortened_candidates) > 1:
            return ("MULTIPLE CANDIDATES", shortened_candidates)

        else:
            return None
    
    return ("MULTIPLE CANDIDATES", candidates)

def get_word_info_from_verse(verse_info, _word):
    word = get_cleaned_alpha_text(_word)
 
    english_word_info = get_word_info(verse_info, word, "english")

    if english_word_info:
        if english_word_info[0] == "MULTIPLE CANDIDATES":
            return None
        return english_word_info[0]

    strongs_usage_info = get_word_info_with_retry_exact(verse_info, word, "strongs_usage")


    if strongs_usage_info:
        if strongs_usage_info[0] == "MULTIPLE CANDIDATES":
            return None
        return strongs_usage_info[0]   

    strongs_ref_usage_info = get_word_info_with_retry_exact(verse_info, word, "ref_strongs_usage")

    if strongs_ref_usage_info:
        if strongs_ref_usage_info[0] == "MULTIPLE CANDIDATES":
            return None
        return strongs_ref_usage_info[0]

    strongs_word_info = get_word_info(verse_info, word, "strongs_options")
    if strongs_word_info:
        if strongs_word_info[0] == "MULTIPLE CANDIDATES":
            return None
        return strongs_word_info[0]

    bdb_word_info = get_word_info_with_retry_exact(verse_info, word, "bdb_options")
    if bdb_word_info:
        if bdb_word_info[0] == "MULTIPLE CANDIDATES":
            return None

        return bdb_word_info[0] # will return none if nothing
    
    # last chance with overall strong text
    strong_text_word_info = get_word_info_with_retry_exact(verse_info, word, "description")
    if strong_text_word_info:
        if strong_text_word_info[0] == "MULTIPLE CANDIDATES":
            return None

        return strong_text_word_info[0] # will return none if nothing
       
