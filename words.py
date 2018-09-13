import nltk
from nltk.probability import ConditionalFreqDist
from nltk.util import ngrams
import random
import re


# get the relevant corpus, etc.
try:
    nltk.data.find('corpora/gutenberg')
except LookupError:
    nltk.download('gutenberg')
nltk.corpus.gutenberg.ensure_loaded()

try:
    nltk.data.find('taggers/universal_tagset')
except LookupError:
    nltk.download('universal_tagset')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class TextGenerator:
    MAXHISTORY = 3

    def __init__(self, corpus=None):
        # use a default words list if no corpus is supplied
        if corpus is None:
            words_list = [
                w for w in nltk.corpus.gutenberg.words(
                    ['burgess-busterbrown.txt', 'carroll-alice.txt',
                     'chesterton-ball.txt'])
                if re.match(r"(?i)^([\w']+|--|[-:;!?.,]$)", w)
            ]
        else:
            words_list = corpus.words()

        if hasattr(corpus, 'tagged_words'):
            tagged_words = corpus.tagged_words(tagset='universal')
        else:
            tagged_words = nltk.pos_tag(words_list, tagset='universal')

        self._scrambled = {}
        self._words_by_tag = self.make_TFD(tagged_words)
        self.cfd = self.make_CFD(words_list)

    def make_TFD(self, tagged_words):
        # setup some frequency distribution dicts
        fd_by_tag = {None: nltk.FreqDist(w[0] for w in tagged_words)}

        words_by_tag = {}

        # classify words by tags
        for word, tag in tagged_words:
            fd_by_tag[tag] = fd_by_tag.get(tag, nltk.FreqDist())
            fd_by_tag[tag][word] += 1

        # set up frequecy dist by tags
        for tag, fd in fd_by_tag.items():
            vals = []
            freq = []
            for v, f in fd.most_common():
                vals.append(v)
                freq.append(f)

            words_by_tag[tag] = (vals, freq)

        return words_by_tag

    def make_CFD(self, words_list):
        ngrams_list = []
        for i in range(2, self.MAXHISTORY + 1):
            ngrams_list += ngrams(words_list, i)
        data = [(tuple(a), b) for *a, b in ngrams_list]

        return ConditionalFreqDist(data)

    def get_random_word(self, tag=None):
        return random.choices(*self._words_by_tag[tag])[0]

    def generate_text_list(self, maxwords, seed):
        for i in range(maxwords):
            for j in range(self.MAXHISTORY - 1, 0, -1):
                if tuple(seed[-j:]) in self.cfd:
                    valuesum = sum(self.cfd[tuple(seed[-j:])].values())
                    value = random.randint(0, valuesum)
                    for key in self.cfd[tuple(seed[-j:])].keys():
                        value -= self.cfd[tuple(seed[-j:])][key]
                        if value <= 0:
                            seed.append(key)
                            break
                    break
                else:
                    continue
        return seed

    def clean_up_text(self, text):
        '''Clean up whitespace before punctuation and weird "'".'''

        return re.sub(
            r'''(?x)
                \s(?=[:;.,!?])
                |
                \s'(?!\s[mdvstl])
                |
                (?<=\w)\s(?=')
                |
                (?<=')\s(?=[mdvstl])
                |
                [-:;,"']$
            ''',
            '', text).strip()

    def generate_text(self, maxwords=100, seed=None):
        while seed is None:
            word = self.get_random_word()
            if word.isalpha():
                seed = [word.capitalize()]

        text = ' '.join(self.generate_text_list(maxwords, seed))
        return self.clean_up_text(text)

    def scramble_word(self, word, tag):
        if word in {'i', 'ii', 'iii', 'iiii',
                    'iv', 'v', 'vi', 'vii', 'viii',
                    'ix', 'x', 'xi', 'xii', 'xiii'}:
            self._scrambled[word] = word.upper()

        elif tag not in {'NOUN', 'ADJ', 'ADV', 'VERB'}:
            self._scrambled[word] = word

        elif len(word) == 1:
            self._scrambled[word] = word.upper()

        else:
            for i in range(10):
                wrd = self.get_random_word(tag=tag)
                if wrd not in self._scrambled.values():
                    break
            self._scrambled[word] = wrd

        return self._scrambled[word]

    def scramble_text(self, title):
        text = nltk.pos_tag(
            re.findall(r"([\w']+|[-:;\.,!\?])", title),
            tagset='universal'
        )
        result = []

        for word, tag in text:
            orig_word = word
            word = word.lower()

            if word not in self._scrambled:
                self.scramble_word(word, tag)

            if orig_word[0].isupper():
                sw = self._scrambled[word]
                if sw.isupper():
                    result.append(sw)
                else:
                    result.append(sw.capitalize())
            else:
                result.append(self._scrambled[word])

        return self.clean_up_text(' '.join(result))

    def generate_title(self, length):
        if length == 1:
            return self.get_random_word(
                tag=random.choices(['NOUN', 'ADJ'], [10, 1])[0])
        elif length >= 2:
            if random.random() < 0.2:
                seed = 'The'
            else:
                seed = self.get_random_word(
                    tag=random.choices(
                        ['ADJ', 'ADV', 'ADP', 'PRT', 'NUM', 'NOUN', 'VERB',
                         'PRON'],
                        [4, 4, 3, 3, 1, 3, 2, 1])[0])

            return self.generate_text(length - 1, [seed])
