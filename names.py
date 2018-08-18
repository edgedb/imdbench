import os.path
import pickle
import random
import requests


class NameGenerator:
    URL = 'https://www2.census.gov/topics/genealogy/1990surnames/'
    MIDDLE_CHANCE = 0.1
    MORE_MIDDLE_CHANCE = 0.01
    MIDDLE_INITIAL_CHANCE = 0.33

    def __init__(self):
        if os.path.exists('names.pickle'):
            # retrieve the pickled names
            with open('names.pickle', 'rb') as f:
                self.names = pickle.load(f)

        else:
            # download the names if not present
            if not os.path.exists('lastnames.txt'):
                with open('lastnames.txt', 'wt') as f:
                    res = requests.get(self.URL + 'dist.all.last')
                    f.write(res.text)
            if not os.path.exists('firstnames_f.txt'):
                with open('firstnames_f.txt', 'wt') as f:
                    res = requests.get(self.URL + 'dist.female.first')
                    f.write(res.text)
            if not os.path.exists('firstnames_m.txt'):
                with open('firstnames_m.txt', 'wt') as f:
                    res = requests.get(self.URL + 'dist.male.first')
                    f.write(res.text)

            self.names = {}
            for cat in ['lastnames', 'firstnames_f', 'firstnames_m']:
                with open(f'{cat}.txt', 'rt') as f:
                    ndict = {'values': [], 'freq': []}
                    self.names[cat] = ndict

                    for line in f:
                        if line:
                            val, fr, _, _ = line.split()
                            ndict['values'].append(val.capitalize())
                            ndict['freq'].append(
                                # convert str float into an int
                                # representing frequency
                                max(1, round(float(fr) * 1000)))

            # pickle generated data
            with open('names.pickle', 'wb') as f:
                pickle.dump(self.names, f)

    def _get_name(self, kind):
        names = self.names[kind]
        return random.choices(names['values'], names['freq'])[0]

    def get_first_name(self, gender=None):
        '''the `gender` argument can be None, "m", or "f".'''

        if gender is None:
            gender = random.choice('mf')

        return self._get_name(f'firstnames_{gender}')

    def get_last_name(self):
        return self._get_name('lastnames')

    def get_middle_name(self, gender=None):
        '''the `gender` argument can be None, "m", or "f".'''

        if gender is None:
            gender = random.choice('mf')

        # middle name is assumed to be from the same pool as
        # firstname, but without any frequency bias (they are all rare)
        return random.choice(self.names[f'firstnames_{gender}']['values'])

    def get_full_name(self, gender=None, *, as_list=False):
        '''the `gender` argument can be None, "m", or "f".'''

        if gender is None:
            gender = random.choice('mf')

        first = self.get_first_name(gender)
        last = self.get_last_name()

        middle = []
        if random.random() < self.MIDDLE_CHANCE:
            while True:
                middle.append(self.get_middle_name(gender))
                if random.random() > self.MORE_MIDDLE_CHANCE:
                    break

        if random.random() < self.MIDDLE_INITIAL_CHANCE:
            middle = [f'{m[0]}.' for m in middle]

        full_name = [first] + middle + [last]

        if as_list:
            return full_name
        else:
            return ' '.join(full_name)
