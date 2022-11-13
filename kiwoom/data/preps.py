"""
Default configuration of how to pre-process raw inputs from the server.
Default way to deal with data is considering one as a string.  

1) prep (default)
    : returns number(x) if possible, else string(x)

2) number
    : returns an int or a float

3) string
    : returns a string with white space removed

4) remove_sign (special case)
    : returns a number/string without any signs (+/-)
"""


def prep(x):
    """
    Preprocess x into number or string (default preprocessor)

    :param x: str
    :return: int/float/str
    """
    try:
        return number(x)
    except ValueError:
        return string(x)


def number(x):
    """
    First, tries to type-cast x into float if it has '.' dot in x. 
    If it fails, move on to int and if fails again retry float.
    If converting to float raises an ValueError, then throws the error.
    """
    if x is None or x.strip() == '':
        return None

    if '.' in x:
        try:
            return float(x)
        except ValueError:
            raise ValueError(f"{x} of type {type(x)} can't be a number.")

    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            raise ValueError(f"{x} of type {type(x)} can't be a number.")


def string(x):
    """
    Returns a string with white space removed.
    """
    return x.strip()


def remove_sign(x):
    """
    Returns number or string with '+' and '-' signs removed.

    1) Removes '+' or '-' from x
    2) Tries to type-cast x into number(int / float)
    3) If step number 2 fails, returns string.
    """
    x = x.translate({ord('+'): '', ord('-'): ''})
    try:
        x = number(x)
    except ValueError:
        x = string(x)
    return x
