from datetime import datetime
from sys import _getframe

from numpy import ndarray
from pandas import Series, Timestamp


# Global Variables
ARRAY_TYPE = (list, tuple, ndarray, Series)


def name():
    """
    Please use inside of a signal/slot method

    :return: the name of the caller, i.e. signal/slot function name
    """
    return _getframe(1).f_code.co_name


def clock():
    """
    Returns current time in format 'HH:MM' of string

    :return: str
    """
    now = datetime.now()
    return f'{now.hour}:{now.minute:02}'


def date(raw):
    """
    :param str:
    :return: datetime.date
    """
    return Timestamp(raw).date()


def list_wrapper(item):
    if item is None:
        return None
    if isinstance(item, ARRAY_TYPE):
        return item
    return [item]


def effective_args(local, remove=None):
    dic = dict(local)

    # Delete 'self' and non effective args
    for param, arg in local.items():
        if arg is None or arg == '':
            del dic[param]
        if param == 'self':
            del dic[param]

    # Delete unwanted args in local
    if remove is not None:
        if isinstance(remove, ARRAY_TYPE):
            for param in remove:
                del dic[param]
        else:
            del dic[remove]

    return dic


def unpack_args(local):
    if 'self' in local:
        del local['self']

    s = ''
    for arg, param in local.items():
        s += str(arg) + '=' + str(param) + ', '
    s = s[:-2] if s else s  # remove last comma and space ', '
    return s
