from collections import defaultdict
from random import randint


MAX_SCREEN_COUNT = 200
MAX_STOCK_PER_SCREEN = 90


class Screen:
    def __init__(self):
        self.config = {
            'opt10079': '4000',  # Stock tick
            'opt10080': '4080',  # Stock min
            'opt10081': '4160',  # Stock day
            'opt10082': '4240',  # Stock week
            'opt10083': '4320',  # Stock month
            'opt10094': '4400',  # Stock year
            'opt20004': '4500',  # Sector tick
            'opt20005': '4580',  # Sector min
            'opt20006': '4660',  # Sector day
            'opt20007': '4740',  # Sector week
            'opt20008': '4820',  # Sector month
            'opt20019': '4900'  # Sector year
        }
        self._used = set()  # assigned screen numbers to TR code
        self._alloc = defaultdict(dict)  # assigned screen number to stock
        self._count = defaultdict(lambda: 0)  # assigned number of stocks to screen number

    def __call__(self, tr_code):
        if tr_code in self:
            self._used.add(self.config[tr_code])
            return self.config[tr_code]

        if len(self._used) >= MAX_SCREEN_COUNT:
            raise RuntimeError(f'The number of screen exceeds maximum limit {MAX_SCREEN_COUNT}.')

        # Assign new random screen number to tr code
        scr_no = str(randint(0, 9999)).zfill(4)
        while scr_no in self:
            scr_no = str(randint(0, 9999)).zfill(4)
        self._used.add(scr_no)
        self.config[tr_code] = scr_no
        return scr_no

    def __contains__(self, key):
        return (key in self.config) or (key in self._used)

    def __delitem__(self, tr_code):
        self._used.remove(tr_code)
        del self.config[tr_code]

    def update(self, tr_code, scr_no):
        self.config[tr_code] = scr_no

    def alloc(self, tr_code, code):
        if code in self._alloc[tr_code]:
            return self._alloc[tr_code][code]

        scr_no = self(tr_code)
        # To check the number of allocated stock/sector exceeds maximum elements per screen
        if self._count[scr_no] >= MAX_STOCK_PER_SCREEN:
            # Try out for the next screen number first
            scr_no = str(int(scr_no.lstrip('0')) + 1).zfill(4)
            # In case next number is already in use
            while scr_no in self:
                rnd = randint(1, 100)
                scr_no = (int(scr_no.lstrip('0')) + rnd) % 10000
                scr_no = str(scr_no).zfill(4)
            self.update(tr_code, scr_no)

        self._alloc[tr_code][code] = scr_no
        self._count[scr_no] += 1
        return self(tr_code)
