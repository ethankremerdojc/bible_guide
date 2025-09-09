import os
from django.core.management.base import BaseCommand, CommandError
from bible_guide.settings import *
import xmltodict
from pprint import pprint
from tqdm import tqdm
import pickle, csv
import re

class Command(BaseCommand):
    pkl_file_paths = [OT_STRONG_PKL_PATH, NT_STRONG_PKL_PATH, OT_MAPPING_PKL_PATH, NT_MAPPING_PKL_PATH]
    
    def get_all_bdb_words(self, bdb_data):

        words = []

        lexicon = bdb_data['lexicon'] # items sorted by letter
        for part in lexicon['part']:

            part_id = part['@id'] # 'a'
            part_title = part['@title'] # '@title': 'א'

            for subsection in part['section']:
                if type(subsection) == str:
                    continue
                ss_id = subsection['@id']

                for word in subsection['entry']:
                    if type(word) == str:
                        continue
                    words.append(word)
        return words

    def get_strong_word_hebrew_text(self, word):
        wd = word['w']
        
        text = wd.get("#text")
        if text:
            return text
        print("unknown strong")
        print(wd)
        raise Exception("unknown word")

    def get_bdb_word_hebrew_text(self, word):
        wd = word['w']

        if type(wd) == list:
            result = []

            for item in wd:
                if type(item) == str:
                    result.append(item)
                else:
                    item_text = item.get("#text")
                    if item_text:
                        result.append(item_text)

            return result

        if type(wd) == str:
            return [wd]

        raise Exception("unknown word")

    def near_match_comparison(self, bdb_words, s_text, s_word):
        # only do this if the other one failed. It will be intensive

        matches = []

        for b_word in bdb_words:
            bdb_text_options = self.get_bdb_word_hebrew_text(b_word)

            for option in bdb_text_options:
                # check if all chars are in there

                #s = ['a', 'd', 'f', 'e']
                #c = ['a', 'b', 'c', 'f', 'e', 'g']
                
                matching_chars = []
                invalid_chars = False

                for char in s_text:
                    if char not in option:
                        invalid_chars = True
                        break

                if not invalid_chars:
                    matches.append((option, b_word))
                    break

        if matches:

            len_sorted = sorted(matches, key=lambda x: len(x[0]))

            best_match = len_sorted[0]

            char_diff = len(best_match[0]) - len(s_text)

            if char_diff == 1:
                return best_match[1]

        return None

    def get_bdb_strong_match(self, stext, s_word, bdb_words):

        b_word = None

        for b_word in bdb_words:
            btext_options = self.get_bdb_word_hebrew_text(b_word)

            if stext in btext_options:
                b_word = b_word
                break

        if not b_word:
            b_word_match = self.near_match_comparison(bdb_words, stext, s_word)
            if not b_word_match:
                return None
            b_word = b_word_match

        return {
            'bdb': b_word,
            'strongs': s_word,
            'bdb_options': self.get_bdb_english_options(b_word),
            'strongs_options': self.get_strongs_english_options(s_word)
        }

    def get_strongs_english_options_base(self, strong_word):
        if not strong_word.get('meaning'):
            return self.get_strongs_english_options(strong_word['reference_words'][0])
        
        if type(strong_word['meaning']) == str:
            return [strong_word['meaning']]

        if not strong_word['meaning'].get('def'):
            return self.get_strongs_english_options(strong_word['reference_words'][0])
        
        if type(strong_word['meaning']['def']) == str:
            return [strong_word['meaning']['def']]
        return strong_word['meaning']['def']

    def get_strongs_english_options(self, strong_word):
        base = self.get_strongs_english_options_base(strong_word)
        # should be a list of strings, but each one may be 
        
        result = []

        for item in base:
            cleaned = re.sub(r"\([^\)]+\)", "", item)
            result.append(cleaned)
        return result


    def get_bdb_english_options(self, bdb_word):
        if not bdb_word.get('def'):
            return []
        if type(bdb_word['def']) == str:
            return [bdb_word['def']]
        return bdb_word['def']

    def add_bdb_to_strongs(self, strongs_words, bdb_words):
        result = {}

        found_count = 0
        not_found_count = 0

        for s_word in tqdm(strongs_words):
            s_id = s_word['@id']
            stext = self.get_strong_word_hebrew_text(s_word) 
            match = self.get_bdb_strong_match(stext, s_word, bdb_words)
            
            if not match:
                if not s_word.get("reference_words"):
                    continue
                
                ref_s_words = s_word['reference_words']

                found = False

                for ref_s_word in ref_s_words:
                    ref_stext = self.get_strong_word_hebrew_text(s_word)
                    ref_match = self.get_bdb_strong_match(ref_stext, ref_s_word, bdb_words)

                    if ref_match:
                        match = ref_match
                        found = True
                        break
                
                if found:
                    result[s_id] = match
                    found_count += 1
                else:
                    result[s_id] = {
                        "bdb": None,
                        "strongs": s_word,
                        "strongs_options": self.get_strongs_english_options(s_word),
                        "bdb_options": []
                    }
                    not_found_count += 1

                # try near matches
                #near_matches = self.near_match_comparison(bdb_words, stext, s_word)
                #not_found_count += 1
                #print("no match for strong word: ", s_word)
            else:
                result[s_id] = match
                found_count += 1

        print("finished matching bdb and strongs.")
        pprint({"not_found": not_found_count, "found": found_count})

        # convert dict to array with index finding for speed
        #for i in range()
        return result

        # list version?
        last_strong_num = int(list(result.keys())[-1].replace("H", ""))

        list_result = []

        for i in range(last_strong_num):
            strong_key = f"H{i + 1}"
            
            item = result.get(strong_key)
            
            if item:
                item["strong_num"] = strong_key
                list_result.append(item)
            else:
                list_result.append(None)

        return list_result

    def get_strong_words(self, strongs_data):
        strong_words = strongs_data["lexicon"]["entry"]
        sw_dict = {}

        #! IMPORTANT
        # All the 9000 strongs words are just punctuation and stuff so we can skip them safely.

        for sw in strong_words:
            sw_dict[sw['@id']] = sw
        
        result = []

        for sw in strong_words:

            sw_num = int(sw['@id'].replace("H", ""))
            if sw_num > 8999:
                print(sw_num)
                continue

            if sw.get("source") and type(sw.get("source")) != str:
                if not sw.get("source").get("w"):
                    continue

                source_word_objs = sw['source']['w']

                if type(source_word_objs) == dict:
                    try:
                        sw['reference_words'] = [sw_dict[source_word_objs['@src']]]
                    except KeyError:
                        pass

                else:
                    source_words = []

                    for w in source_word_objs:
                        try:
                            sw_id = w['@src']
                            source_words.append(sw_dict[sw_id])
                        except KeyError:
                            pass

                    sw['reference_words'] = source_words

            result.append(sw)

        return result

    def get_or_create_merged_bdb_strongs(self):

        pklfile_path = OT_STRONG_PKL_PATH

        if os.path.exists(pklfile_path):
            with open(pklfile_path, 'rb') as pklfile:
                return pickle.load(pklfile)

        hebrew_bdb_file = "openbib/HebrewLexicon/BrownDriverBriggs.xml"
        hebrew_strongs_file = "openbib/HebrewLexicon/HebrewStrong.xml"

        with open(hebrew_bdb_file) as f:
            bdb_data = xmltodict.parse(f.read())
        with open(hebrew_strongs_file) as f:
            strongs_data = xmltodict.parse(f.read())
        
        bdb_words = self.get_all_bdb_words(bdb_data)
        strong_words = self.get_strong_words(strongs_data)
        
        merged_data = self.add_bdb_to_strongs(strong_words, bdb_words)
        
        with open(pklfile_path, 'wb') as pklfile:
            pickle.dump(merged_data, pklfile)

        return merged_data

    def get_or_create_ot_strongs_mapping(self):

        pklfile_path = OT_MAPPING_PKL_PATH

        if os.path.exists(pklfile_path):
            with open(pklfile_path, 'rb') as pklfile:
                return pickle.load(pklfile)

        mapping_csv_file = "openbib/hebrew_csvs/BHSA-8-layer-interlinear.csv"

        rows = []

        with open(mapping_csv_file, newline='') as f:

            reader = csv.reader(f, delimiter='\t')

            for row in reader:
                rows.append(row)

        books = {}

        for row in rows[1:]:
            __kjvverseid, book_id, chapter_id, verse_id = row[1].split("｜")
            verse_id = verse_id[:-1]
            lexem_id = row[6]
            strong_num = row[7]

            if "H" not in strong_num:
                # other broken stuff
                continue

            # if this strong num is one of the 9000 ones, we skip it, punctuation or something
            num_sn = int(strong_num.replace("H", ""))
            if num_sn > 8999:
                continue

            if not books.get(book_id):
                books[book_id] = {}

            if not books[book_id].get(chapter_id):
                books[book_id][chapter_id] = {}

            if not books[book_id][chapter_id].get(verse_id):
                books[book_id][chapter_id][verse_id] = {
                    'strongs': [],
                    'lexems': [],
                }
            
            if strong_num not in books[book_id][chapter_id][verse_id]['strongs']:
                books[book_id][chapter_id][verse_id]['strongs'].append(strong_num)
                books[book_id][chapter_id][verse_id]['lexems'].append(lexem_id)

        with open (pklfile_path, 'wb') as pklfile:
            pickle.dump(books, pklfile)

        return books

    def populate_ot(self):
        print("getting or creating merged bdb strongs data")
        merged_data = self.get_or_create_merged_bdb_strongs()
        print("Getting ot mapping")
        ot_mapping = self.get_or_create_ot_strongs_mapping()

    def get_nt_strongs_data(self):
        csv_file_path = "openbib/greek_csvs/OpenGNT_DictOGNT.csv"
 
        pklfile_path = NT_STRONG_PKL_PATH

        if os.path.exists(pklfile_path):
            with open(pklfile_path, 'rb') as pklfile:
                return pickle.load(pklfile)

        strong_words = {}

        with open(csv_file_path) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')

            for row in reader:
                strong_num = row[0]
                info_data = row[1]
                strong_words[strong_num] = info_data

        with open(pklfile_path, 'wb') as pklfile:
            pickle.dump(strong_words, pklfile)

        return strong_words

    def get_nt_strongs_mapping(self):
        mapping_file = "openbib/greek_csvs/OpenGNT_version3_3.csv"

        pklfile_path = NT_MAPPING_PKL_PATH

        if os.path.exists(pklfile_path):
            with open(pklfile_path, 'rb') as pklfile:
                return pickle.load(pklfile)

        rows = []

        with open(mapping_file) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')

            for row in reader:
                rows.append(row)

        books = {}

        for row in rows:
            book_id, chapter_id, verse_id = row[6].replace("〔", "").replace("〕", "").split("｜")
            _a, _b, _c, lexem_id, _d, strong_num = row[7].replace("〔", "").replace("〕", "").split("｜")

            if not books.get(book_id):
                books[book_id] = {}

            if not books[book_id].get(chapter_id):
                books[book_id][chapter_id] = {}

            if not books[book_id][chapter_id].get(verse_id):
                books[book_id][chapter_id][verse_id] = {
                    'strongs': [],
                    'lexems': []
                }
            
            books[book_id][chapter_id][verse_id]['strongs'].append(strong_num)
            books[book_id][chapter_id][verse_id]['lexems'].append(lexem_id)

        with open (pklfile_path, 'wb') as pklfile:
            pickle.dump(books, pklfile)

        return books

    def populate_nt(self):
        print("Getting NT strongs data")
        strongs_data = self.get_nt_strongs_data()
        print("Getting NT strongs mapping")
        strongs_mapping = self.get_nt_strongs_mapping()

    def add_arguments(self, parser):
        parser.add_argument('-r', '--refresh', action="store_true")

    def handle(self, *args, **kwargs):
    
        if kwargs.get("refresh"):
            for path in self.pkl_file_paths:
                if os.path.exists(path):
                    os.remove(path)

        self.populate_ot()
        self.populate_nt()
