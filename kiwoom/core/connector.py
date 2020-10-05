from functools import wraps
from textwrap import dedent
from types import LambdaType
from inspect import (
    getfullargspec,
    getattr_static,
    ismethod,
    isfunction,
    isclass,
    ismodule
)


class Connector:
    """
    Decorator class
    """
    warn = True

    def __init__(self, key=None):
        self.key = key

    def __call__(self, ehandler):
        @wraps(ehandler)  # keep docstring of event handler
        def wrapper(*args):
            """
            Decorator for connecting event handler to the right slots
              >> @Connector()
              >> def event_handler(*args):

            :param ehandler: event handler of empty method in Kiwoom class
            :return: wrapped function that executes slot with given args
            """

            # To execute the default event handler
            ehandler(*args)

            api = args[0]  # instance of Kiwoom class
            if self.key is not None:
                key = getfullargspec(ehandler).args.index(self.key)
                try:
                    slot = api.slot(self.key)
                    slot(*args[1:])
                except KeyError:
                    msg = dedent(
                        f"""\n
                        Event handler {ehandler.__name__} is not connected to any slot with key '{key}'.
                        Please try to connect signal and slot first by using kiwoom.connect() method.
                        
                          >> api.connect(signal, slot, key)  # api = Kiwoom()
                        """
                    )
                    raise RuntimeError(msg)

            else:
                key = ehandler.__name__
                try:
                    slot = api.slot(key)
                    slot(*args[1:])
                except KeyError:
                    if Connector.warn:
                        msg = dedent(
                            f"""
                            kiwoom.{key}({', '.join(map(str, args[1:]))}) has been called.

                            But the event handler, '{ehandler.__name__}', is not connected to any slot.
                            Please try to connect slot and event by using kiwoom.connect() method.
                            
                              >> api.connect(slot=slot_method, event='{key}')  # api = pykiwoom.Kiwoom()

                            This warning message can disappear by the following.

                              >> pykiwoom.Connector.mute(True)  # class method
                            """
                        )
                        print(msg)
                        # raise RuntimeWarning(msg)
        return wrapper

    @classmethod
    def mute(cls, bool):
        cls.warn = not bool

    @staticmethod
    def connectable(fn):
        # Instance method, Class method
        if ismethod(fn):
            return True

        # Normal function, Class function, Lambda function
        if isfunction(fn):
            # Lambda function
            if isinstance(fn, LambdaType):
                return True

            qname = getattr(fn, '__qualname__')
            if '.' in qname:
                idx = qname.rfind('.')
                prefix, fname = qname[:idx], qname[idx + 1:]
                obj = eval(prefix)

                # Normal function
                if ismodule(obj):
                    return True

                # Class function
                if isclass(obj):

                    # Static method
                    if isinstance(getattr_static(obj, fname), staticmethod):
                        return True

                    # Class function should be bound to an instance
                    if not hasattr(fn, '__self__'):
                        raise ValueError(dedent(
                            f"""
                                Given '{fname}' must be instance method, not function.
                                Try to make an instance first as followings.
    
                                  >> var = {prefix}(*args, **kwargs)
                                  >> kiwoom.connect(.., var.{fname}, ..)
                                """
                        ))  # False

        # Just a callable object (a class that has '__call__')
        elif callable(fn):
            # Static call
            if isinstance(getattr_static(fn, '__call__'), staticmethod):
                return True

            # Non-static call should be bound to an instance
            if not hasattr(fn, '__self__'):
                raise ValueError(dedent(
                    f"""
                        Given '{getattr(fn, '__qualname__')} must be bound to instance.
                        Try to make an instance first as followings.
    
                          >> var = {getattr(fn, '__name__')}(*args, **kwargs)
                          >> kiwoom.connect(.., var, ..)
                    """
                ))  # False

        # Not a valid argument
        else:
            from kiwoom.core.kiwoom import Kiwoom  # Dynamic import to avoid circular import
            raise ValueError(
                f"Unsupported type, {type(fn)}. Please try with valid args.\n\n{help(Kiwoom.connect)}."
            )  # False
