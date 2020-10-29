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
    This class helps mapping events to specific slots. If event is called,
    then wrapper function automatically calls slots with the same args.
    """
    warn = True

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, ehandler):
        """
        Decorator for connecting event to the right slot
          # Usage
          >> @Connector()
          >> def event_handler(*args):

        :param ehandler: event handler of empty method in Kiwoom class
        :return: a wrapped function that can execute connected slot with given args
        """
        @wraps(ehandler)  # keep docstring of event handler
        def wrapper(api, *args):
            # To execute the default event handler in case of overriding
            ehandler(api, *args)

            # Variables
            event = getattr(ehandler, '__name__')
            hook = api.get_connect_hook(event)

            # To find connected slot
            try:
                # If hook is set on the event, then key becomes arg that corresponds to the hook
                # ex) if hook is rq_name for on_receive_tr_data, then key becomes an arg passed into rq_name
                key = args[getfullargspec(ehandler).args.index(hook) - 1] if hook else None
                # To retrieve the right slot
                slot = api.slot(event, key)
            except KeyError:
                if Connector.warn:
                    msg = dedent(
                        f"""
                        kiwoom.{event}({', '.join(map(str, args[1:]))}) has been called.
    
                        But the event handler, '{event}', is not connected to any slot.
                        Please try to connect event and slot by using kiwoom.connect() method.
                          >> api.connect('{event}', slot=slot_method)
    
                        This warning message can disappear by the following.
                          >> from kiwoom import Connector 
                          >> Connector.mute(True)  # class method
                        """
                    )
                    print(msg)
                return wrapper

            # To execute the connected slot
            slot(*args)
        return wrapper


    @classmethod
    def mute(cls, bool):
        cls.warn = not bool

    @staticmethod
    def connectable(fn):
        """
        if
        :param fn: method to connect
        :return:
        """
        # None
        if fn is None:
            return False

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
                f"Unsupported type, {type(fn)}. Please try with valid args.\n\n{Kiwoom.connect.__doc__}."
            )  # False
