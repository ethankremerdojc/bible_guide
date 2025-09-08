import os
from django.core.management.base import BaseCommand, CommandError
from bible_guide.settings import VERSIONS_DIR
import xmltodict
from pprint import pprint
from tqdm import tqdm
import pickle, csv
import re

class Command(BaseCommand):
    
    def get_all_bdb_words(self, bdb_data):

        words = []

        lexicon = bdb_data['lexicon'] # items sorted by letter
        for part in lexicon['part']:

            # items grouped by first letter

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
                    
                    #if type(word) == str:
                    #    continue

                    #bdb_id = word.get('@id')
                    #hebrew_text_options = word['w']
                    #bdb_name = word.get('def')

                    #if word.get('#text'):
                    #    bdb_definitions = [word['#text']]
                    #else:
                    #    # should be sense
                    #    sense = word.get('sense')
                    #    definitions = []
                    #    for s in sense:



                    #bdb_word = {
                    #    'bdb_id': bdb_id,
                    #    'bdb_hebrew_text_options': hebrew_text_options,
                    #    'bdb_name': bdb_name,
                    #    'bdb_definitions': bdb_definitions
                    #}
                    #words.append(bdb_word)
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
        for b_word in bdb_words:
            btext_options = self.get_bdb_word_hebrew_text(b_word)

            #if b_word['@id'] == "a.ac.ae":
            #    print(b_word)

            if stext in btext_options:
                return {
                    'bdb': b_word,
                    'strongs': s_word
                }

        # still no match, check for 1 char off near match
        return self.near_match_comparison(bdb_words, stext, s_word)

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
                        "strongs": s_word
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
        return result

    def get_strong_words(self, strongs_data):
        strong_words = strongs_data["lexicon"]["entry"]
        sw_dict = {}

        for sw in strong_words:
            sw_dict[sw['@id']] = sw
        
        result = []

        for sw in strong_words:
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

        pklfile_path = "OT_strong_data.pkl"

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

    def get_or_create_strongs_mapping(self):

        pklfile_path = "OT_book_mapping.pkl"

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

    def populate_ot(self):
        #〔H9003｜c1｜1｜E70001｜in〕〔H7225｜c1｜2｜E70002｜beginning〕〔H1254｜c1｜3｜E70003｜create〕〔H430｜c1｜4｜E70004｜god(s)〕〔H853｜c1｜5｜E70005｜[object marker]〕〔H9009｜c1｜6｜E70006｜the〕〔H8064｜c1｜7｜E70007｜heavens〕〔H9000｜c1｜8｜E70008｜and〕〔H853｜c1｜9｜E70005｜[object marker]〕〔H9009｜c1｜10｜E70006｜the〕〔H776｜c1｜11｜E70009｜earth〕
        print("getting or creating merged bdb strongs data")
        merged_data = self.get_or_create_merged_bdb_strongs()
        print("Getting verse by verse mapping")
        ot_mapping = self.get_or_create_strongs_mapping()
        print(ot_mapping['1']['1']['1'])

    def get_nt_strongs_data(self):
        csv_file_path = "openbib/greek_csvs/OpenGNT_DictOGNT.csv"
 
        pklfile_path = "NT_strong_data.pkl"

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

        pklfile_path = "NT_book_mapping.pkl"

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
        strongs_data = self.get_nt_strongs_data()
        strongs_mapping = self.get_nt_strongs_mapping()

    def handle(self, *args, **kwargs):
        self.populate_ot()
        self.populate_nt()
