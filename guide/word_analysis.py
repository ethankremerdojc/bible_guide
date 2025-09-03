import requests
import json
from bs4 import BeautifulSoup, NavigableString

def get_cleaned_alpha_text(text):
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
    return "".join(t for t in text.lower() if t in allowed_chars)

def get_text_biblegateway(book, chapter, version):
    url = f"https://www.biblegateway.com/passage/?search={book}%20{chapter}&version={version}"
    response = requests.get(url)
    response.encoding = "utf-8"
    response_text = response.text

    soup = BeautifulSoup(response_text, "html.parser")
    chapter_contents = soup.find('div', class_="result-text-style-normal")

    text_blocks = chapter_contents.select("p .text")

    result = ""

    for block in text_blocks:

        parts = []
        for child in block:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif child.name == "span" and "woj" in child.get("class", []):
                child_text_nodes = child.find_all(string=True, recursive=False)
                parts.append("".join(child_text_nodes).strip())

        joined_parts = "".join(parts).strip()
        result += joined_parts + "\n"

    result = result [:-1] # get rid of last \n

    return result

def get_chapter_bible_hub(book_name, chapter_num):
    url = f"https://biblehub.com/interlinear/{book_name}/{chapter_num}.htm"
    response = requests.get(url)
    response.encoding = "utf-8"
    response_text = response.text

    soup = BeautifulSoup(response_text, "html.parser")
    chapter_contents = soup.select(".chap")[0]

    verses = []
    current_verse = None
    
        
    for table_data in chapter_contents.select(".tablefloat td"):
        strong_num = table_data.find("span", class_="pos").get_text()
        strong_text = table_data.find("span", class_="pos").find("a").attrs['title']
        original_language = table_data.find("span", class_="greek").get_text() #TODO need to select other languages
        english_literal = table_data.find("span", class_="eng").get_text()

        word_info = {
            "strong_num": strong_num,
            "strong_text": strong_text[strong_text.index(":") + 2:], # everything after : in Strongs Greek 1234: ...
            "original_language": original_language,
            "english": get_cleaned_alpha_text(english_literal.replace("\xa0", " "))
        }
        
        try:
            verse_num = table_data.find("span", class_="refmain").get_text().replace("\xa0", "")
            
            if current_verse is not None:
                verses.append(current_verse)

            current_verse = {
                "num": verse_num,
                "words": []
            }
        except AttributeError:
            pass

        current_verse["words"].append(word_info)

    verses.append(current_verse)

    result = {}

    for v in verses:
        result[v["num"]] = v["words"]

    return result
