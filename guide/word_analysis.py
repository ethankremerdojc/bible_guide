import requests
import json
from bs4 import BeautifulSoup, NavigableString
from pprint import pprint
import re
def get_cleaned_alpha_text(text):
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
    return "".join(t for t in text.lower() if t in allowed_chars)

def get_text_biblegateway(book, chapter, version):
    url = f"https://www.biblegateway.com/passage/?search={book.replace(" ", "+")}%20{chapter}&version={version}"
    response = requests.get(url)
    response.encoding = "utf-8"
    response_text = response.text

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

def get_chapter_bible_hub(book_name, chapter_num):
    url = f"https://biblehub.com/interlinear/{book_name.replace(' ', '_')}/{chapter_num}.htm"
    response = requests.get(url)
    response.encoding = "utf-8"
    response_text = response.text

    soup = BeautifulSoup(response_text, "html.parser")
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

        strong_num = table_data.find("span", class_=posname).get_text()
        try:
            strong_text = table_data.find("span", class_=posname).find("a").attrs['title']
        except AttributeError: # weird punctuation
            continue
        original_language = table_data.find("span", class_=language).get_text() #TODO need to select other languages
        english_literal = table_data.find("span", class_="eng").get_text()

        word_info = {
            "strong_num": strong_num,
            "strong_text": strong_text[strong_text.index(":") + 2:], # everything after : in Strongs Greek 1234: ...
            "original_language": original_language,
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

        current_verse["words"].append(word_info)

    verses.append(current_verse)

    result = {}

    for v in verses:
        result[v["num"]] = v["words"]

    return result
