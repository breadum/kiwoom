from collections import defaultdict


TYPES = ('single', 'multi')


class Share:
    """
    Share Class handles common data shared between Signals and Slots

    There are 4 types of data.
    1. args
    2. single
    3. multi
    4. history

    Each of data has 3 methods.
    1. get
    2. remove
    3. update/extend

    Dictionary-like 4 methods in common for single and multi data.
    1. keys
    2. has_key
    3. get
    4. items
    """
    def __init__(self):
        self.args = dict()
        self.single = defaultdict(dict)
        self.multi = defaultdict(lambda: defaultdict(list))
        self.history = defaultdict(lambda: defaultdict(list))

    """
    Dictionary-like Methods
    """
    def keys(self, typ, fn=None):
        """
        Returns keys stored for given fn.         
        
        :param typ: str
            must be one of ('single', 'multi')
        :param fn: str or None
            method name used when calling one of updating methods
            if fn is None, returns all 'fn' stored 
        """
        if typ.lower() not in TYPES:
            raise KeyError(f"Given type must be one of {TYPES}, not '{typ}'.")
        
        dic = getattr(self, typ)
        if fn is None:
            return dic.keys()
        if fn in dic:
            return dic[fn].keys()
        raise KeyError(f"Given fn, '{fn}', is not in {typ} data.")

    def has_key(self, typ, fn, key=None):
        """
        Returns if key stored in fn of given typ. 
        
        :param typ: str
            must be one of ('single', 'multi')
        :param fn: str
            method name used when calling one of updating methods
        :param key: str or None
            key that needs to be checked whether or not it is stored
            if key is None, check whether fn is stored in share or not
        """
        if key is None:
            return fn in self.keys(typ)
        return key in self.keys(typ, fn)

    def get(self, typ, fn, key=None):
        """
        Returns if key stored in fn of given typ.
        
        :param typ: str
            must be one of ('single', 'multi')
        :param fn: str
            method name used when calling one of updating methods
        :param key: str or None
            key that needs to be checked whether or not it is stored
            if key is None, get whole data stored for fn
        """
        if self.has_key(typ, fn, key):
            dic = getattr(self, typ)
            if key is None:
                return dic[fn]
            return dic[fn][key]
        
        # Raise an error
        if self.has_key(typ, fn):
            raise KeyError(f"Given key, '{key}', is not in {typ} data.")
        raise KeyError(f"Given fn, '{fn}', is not in {typ} data.")

    def items(self, typ, fn):
        """
        Returns a dict_items with (key, val) pairs for given fn. 

        :param typ: str
            must be one of ('single', 'multi')
        :param fn: str
            method name used when calling one of updating methods
        """
        dic = self.get(typ, fn)
        return dic.items()

    """
    Arg Data
    """
    def isin_args(self, fn, key=None):
        if key is None:
            return fn in self.args
        return key in self.args[fn]

    def get_args(self, fn, key=None):
        if key is None:
            return self.args[fn]
        return self.args[fn][key]

    def update_args(self, fn, args):
        self.args[fn] = args

    def remove_args(self, fn):
        if fn in self.args:
            del self.args[fn]

    """
    Single Data
    """
    def isin_single(self, fn, key=None):
        return self.has_key('single', fn, key)

    def get_single(self, fn, key=None):
        return self.get('single', fn, key)

    def update_single(self, fn, key, val):
        self.single[fn][key] = val

    def remove_single(self, fn, key=None):
        if key is None:
            if fn in self.single:
                del self.single[fn]
            return
        if fn in self.single:
            if key in self.single[fn]:
                del self.single[fn][key]

    """
    Multi Data
    """
    def isin_multi(self, fn, key=None):
        return self.has_key('multi', fn, key)

    def get_multi(self, fn, key=None):
        return self.get('multi', fn, key)

    def extend_multi(self, fn, key, vals):
        # To Extend list to original data
        self.multi[fn][key] += vals

    def remove_multi(self, fn):
        if fn in self.multi:
            del self.multi[fn]

    """
    History Data
    """
    def get_history(self, code=None, key=None):
        if code is None:
            return self.history
        elif key is None:
            return self.history[code]
        return self.history[code][key]

    def extend_history(self, code, key, vals):
        # To Extend list to original data
        self.history[code][key] += vals

    def remove_history(self, code):
        if code in self.history:
            del self.history[code]
