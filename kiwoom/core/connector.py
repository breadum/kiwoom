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
    Decorator class for mapping empty events to user implementing slots.

    This class helps mapping events to specific slots. 'Kiwoom' instance
    contains mapping information which had been set from two methods.

    1) Kiwoom.connect(event, signal, slot)
    2) Kiwoom.set_connect_hook(event, param)

    This decorator does not contain those mapping information but only
    uses the one defined in instance. This is because decorator should
    work on various contexts. The first parameter of wrapper function
    in __call__ method, i.e. api, is 'self' argument for Kiwoom object.

    This class has three main methods.
    1) Connector.__call__(event)
      - act as a decorator for pre-defined Kiwoom events
      - below is the usage example

        class Kiwoom(API):
            ...
            @Connector()
            def on_event_connect(self, err_code):
                pass
            ...

    2) Connector.mute(bool)  # static method
      - warning message can be turned on/off.

    3) Connector.connectable(fn)  # static method
      - Check if given fn is a bounded method to an instance.
      - If fn is not a bounded method, it should be static or lambda.
      - Bounded method is important to handle continuous information
    """
    # Class variable
    warn = True

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, ehandler):
        """
        Decorator method to call slot method when event connected to slot has been called.

        When event has been called, this decorator method is called with event method as arg.
        Then wrapper function wraps the event and then the function is returned to be called.

        Inside the wrapper, it takes all args from the event. The First arg is 'self' which is
        an instance of Kiwoom class. The rest of args depends on which event has been called.

        Firstly, execute event handler which is initially an empty method in the module. But
        this process is needed when an empty method is overridden. Then, find the right slot
        connected to the event. If found, execute it with the same args forwarded from event.
        If not, just print a warning message. This message can be turned on/off.

        Usage example
        >>  class Kiwoom(API):
        >>      ...
        >>      @Connector()  # decorator
        >>      def on_event_connect(self, err_code):
        >>          pass  # empty event
        >>      ...

        :param ehandler: method
            One of pre-defined event handlers, see kiwoom.config.events.
        :return: function
            Wrapper function that executes a slot method connected to the event.
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
        """
        Class method to turn on/off printing warning message of no connected slot to an event.

        Usage example
        >> Connector.mute(True/False)

        :param bool: bool
            If True, no warning message else warning.
        """
        cls.warn = not bool

    @staticmethod
    def connectable(fn):
        """
        Static function that checks given fn is callable and bounded method.

        When event is called, a slot mapped to the event is to be called by decorator.
        If fn is not a static function nor lambda function, fn needs 'self' argument to
        work correctly. This is why fn should be bounded method to instance object.
        Bounded method contains 'self' argument by itself. This method is used in
        Kiwoom.connect(event, signal, slot) to check validity before making connections.
        When given fn is not valid to connect, this function raises TypeError.

        :param fn: method, function or None
            Any callables to be tested. None is exceptionally accepted.
        :return: bool
            If a callable can be executed without any problem, returns True.
        """
        # None by default False
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
                        raise TypeError(dedent(
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
                raise TypeError(dedent(
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
            raise TypeError(
                f"Unsupported type, {type(fn)}. Please try with valid args.\n\n{Kiwoom.connect.__doc__}."
            )  # False
