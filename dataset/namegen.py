import pathlib
import random


class NameGenerator:

    MIDDLE_CHANCE = 0.1
    MORE_MIDDLE_CHANCE = 0.01
    MIDDLE_INITIAL_CHANCE = 0.33

    # paths where various data files may be expected/placed
    vendror_path = pathlib.Path(__file__).resolve().parent / 'vendor'

    files = {
        'lastnames': vendror_path / 'dist.all.last',
        'firstnames_f': vendror_path / 'dist.female.first',
        'firstnames_m': vendror_path / 'dist.male.first',
    }

    def __init__(self):
        self.names = {}
        for cat, path in self.files.items():
            with open(path, 'rt') as f:
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
