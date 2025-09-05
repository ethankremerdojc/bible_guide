import os
from django.core.management.base import BaseCommand, CommandError
from bible_guide.settings import VERSIONS_DIR
import xmltodict
from pprint import pprint
from tqdm import tqdm

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
        input()

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

        print("unknown bdb")
        print(word['w'])
        input()

    def near_match_comparison(bdb_words, s_text):
        # only do this if the other one failed. It will be intensive
        
        matches = []
        


        for b_word in bdb_words:
            bdb_text_options = self.get_bdb_word_hebrew_text(b_word)

            for option in bdb_text_options:
                # check if all chars are in there
                for char in s_text:
                    if char in option:
                        # compare the two lists to see if they are 'close enough'

    def add_bdb_to_strongs(self, strongs_words, bdb_words):
        result = []

        for s_word in tqdm(strongs_words):
            stext = self.get_strong_word_hebrew_text(s_word)
            found = False

            for b_word in bdb_words:
                btext_options = self.get_bdb_word_hebrew_text(b_word)

                if stext in btext_options:

                    combined = {
                        'bdb': b_word,
                        'strongs': s_word
                    }
                    result.append(combined)
                    found = True

            if not found:
                print("no match for strong word: ", s_word)
                input()



    def populate_ot(self):
        hebrew_bdb_file = "openbib/HebrewLexicon/BrownDriverBriggs.xml"
        hebrew_strongs_file = "openbib/HebrewLexicon/HebrewStrong.xml"

        with open(hebrew_bdb_file) as f:
            bdb_data = xmltodict.parse(f.read())
        with open(hebrew_strongs_file) as f:
            strongs_data = xmltodict.parse(f.read())
        
        bdb_words = self.get_all_bdb_words(bdb_data)
        strong_words = strongs_data["lexicon"]["entry"]
        
        complete_data = self.add_bdb_to_strongs(strong_words, bdb_words)
        # add all the bdb data to the strong words
    
    def handle(self, *args, **kwargs):
        self.populate_ot() 
