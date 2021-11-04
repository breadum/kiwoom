from functools import wraps
from textwrap import dedent
from types import LambdaType
from inspect import (
    getattr_static,
    isclass,
    isfunction,
    ismethod,
    ismodule
)

from kiwoom import config
from kiwoom.config import valid_event


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
    1) Connector.map(event)
      - act as a decorator for pre-defined Kiwoom events
      - below is the usage example

        class Kiwoom(API):
            ...
            @map
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
    nargs = {
        'on_event_connect': 1,
        'on_receive_msg': 4,
        'on_receive_tr_data': 5,
        'on_receive_real_data': 3,
        'on_receive_chejan_data': 3,
        'on_receive_condition_ver': 2,
        'on_receive_tr_condition': 5,
        'on_receive_real_condition': 4
    }

    def __init__(self):
        # If no hook is set, dic[event] returns signal/slot.
        # If hook is set, dic[event][key] returns signal/slot.
        self._hooks = dict()
        self._signals = dict()
        self._slots = dict()
        self._indices = dict()

    def signal(self, event, key=None):
        """
        Returns signal methods connected to the event.

        If signal and slot are connected to a specific event by Kiwoom.connect() method,
        then this method returns the connected signal method. If signal is not connected,
        or wrong key is given, raise a KeyError.

        'key' is needed when hook is set by Kiwoom.set_connect_hook(). 'key' is set to
        be the name of signal method by default unless another string is set on purpose
        when connecting.

        When requesting data to server is needed, specifically if more data is available,
        Kiwoom.signal() returns the exact signal method that can request more data.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :param key: str, optional
            If hook is set by Kiwoom.set_connect_hook() method and signal is connected
            by Kiwoom.connect(), then key is needed. 'key' is set to be name of the
            signal method by default unless another 'key' is given when connecting.
        :return: method
            Signal method connected to the given event. If wrong event, returns None.
        """
        if not valid_event(event):
            return None
        if not self.connect_hook(event):
            return self._signals[event]
        return self._signals[event][key]

    def slot(self, event, key=None):
        """
        Returns slot methods connected to the event.

        If signal and slot are connected to specific event by Kiwoom.connect() method,
        then this method returns the connected slot method. If slot is not connected,
        or wrong key is given, this raises a KeyError.

        'key' is needed when hook is set by Kiwoom.set_connect_hook(). 'key' is set to
        be the name of slot method by default unless another string is set on purpose
        when connecting.

        When an event is called, Kiwoom.slot() returns the exact slot method that can
        handle data received from the event. This method is used in Connector decorator
        that wraps events to execute connected slot with the event.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :param key: str, optional
            If hook is set by Kiwoom.set_connect_hook() method and slot is connected
            by Kiwoom.connect(), then key is needed. 'key' is set to be name of the
            slot method by default unless another 'key' is given when connecting.
        :return: method or None
            Slot method connected to the given event. If wrong event, returns None.
        """
        if not valid_event(event):
            return None
        if not self.connect_hook(event):
            return self._slots[event]
        return self._slots[event][key]

    def connect(self, event, signal=None, slot=None, key=None):
        """
        Connects signals and slots to one of pre-defined events.

        Information saved in this method is used by decorator @Connector() which wraps
        the events and automatically calls the right slot connected to the events. In
        addition to the decorator, Kiwoom.signal(event, key) and Kiwoom.slot(event, key)
        returns the one connected to the event.

        1) If no hook is set on the event, then the connected signal/slot can be retrieved
           by Kiwoom.signal(event) and Kiwoom.slot(event). There is no need to use key.

        2) If hook is set by Kiwoom.set_connect_hook() on the event, in which case there
           needs multiple slots to connect on one event, then connection requires a key
           which is to be the name of signal/slot methods by default.

           The convention to utilizing this module recommends to define the name of related
           signal and slot to be the same. Then it becomes easier to manage and develop codes.

           Use 'key' arg only when there is a special need. The connected signal/slot can be
           retrieved by Kiwoom.signal(event, key='name') and Kiwoom.slot(event, key='name').
           Here 'name' can be a method name or special 'key' used in this method.

        This method checks whether or not given signal/slot can be called without any
        problem. If given method is not bounded to an instance, method should be static
        or lambda function. This is because normally 'self' argument is needed to call
        methods, therefore method must be bounded to an instance unless given method is
        a function.

        Please see tutorials example on the link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/4.%20TR%20Data.py

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :param signal: method, optional
            A method that requests to the server
        :param slot: method, optional
            A method that reacts the server's response
        :param key: str, optional
            Key is needed only if hook is set by Kiwoom.set_connect_hook() method.
            Key is set to be name of the given signal and/or slot method by default.
            If key is given other than method name, the connected signal can be
            retrieved by Kiwoom.siganl(event, key) and slot by Kiwoom.slot(event, key)
        """
        valid = False
        connectable = Connector.connectable

        if not valid_event(event):
            return

        # Directly connect slot to the event
        if not self.connect_hook(event):
            # Key can't be used here
            if key is not None:
                raise RuntimeError(
                    "Key can't be used. Remove key argument or Try to set_connect_hook() first."
                )

            elif connectable(signal):
                if connectable(slot):
                    valid = True
                    self._signals[event] = signal
                    self._slots[event] = slot

            elif connectable(slot):
                valid = True
                self._slots[event] = slot

        # Connect slot to the event when connect hook is already set
        else:
            if connectable(signal):
                if connectable(slot):
                    valid = True
                    # Key other than method's name
                    if key is not None:
                        self._signals[event][key] = signal
                        self._slots[event][key] = slot
                    # Default key is method's name
                    else:
                        self._signals[event][getattr(signal, '__name__')] = signal
                        self._slots[event][getattr(slot, '__name__')] = slot

            elif connectable(slot):
                valid = True
                if key is not None:
                    self._slots[event][key] = slot
                else:
                    self._slots[event][getattr(slot, '__name__')] = slot

        # Nothing is connected
        if not valid:
            raise RuntimeError(f"Unsupported combination of inputs. Please read below.\n\n{self.connect.__doc__}")

    def connect_hook(self, event):
        """
        Returns whether a hook is set for the given event.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :return: bool
        """
        if event in self._hooks:
            return True
        return False

    def set_connect_hook(self, event, param):
        """
        Set parameter defined in event as a hook to find the right slot when event is called.

        When an event needs multiple slots to connect, depending on specific tasks, set
        a hook(key) to select which slot to map. The hook must be one of the parameters
        in the definition of the event method. Parameters can be found by help built-in
        function or Kiwoom.api_arg_spec(event). This raises a KeyError if given param is
        not defined in event method.

        If hook is set to the given parameter, argument passed into the parameter when
        the event is called, is going to be a key to connect event, signal and slot.

        Convention is that the name of signal and slot that deal with the related task
        is recommended to be the same, so that 'key' is set to be the method name of
        signal and slot by default. See examples on the tutorials link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/5.%20TR%20Data.py

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :param param: str
            Parameter name defined in given event. To see all parameters to event,
            use Kiwoom.api_arg_spec(event) method or help(...) built-in function.
        """
        if not valid_event(event):
            return

        # To check given arg is valid
        from kiwoom import Kiwoom  # lazy import
        args = Kiwoom.api_arg_spec(event)
        if param not in args:
            raise KeyError(f"{param} is not valid.\nSelect one of {args}.")

        # To set connect hook and its index in args
        self._hooks[event] = param
        self._indices[event] = list(args.keys()).index(param) - 1  # except 'self'

        # Initialize structure to get signal/slot method by dic[event][key]
        self._signals[event] = dict()
        self._slots[event] = dict()

    def get_connect_hook(self, event):
        """
        Returns a hook (i.e. name of parameter) set in given event.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        :return: str or None
            If exists, returns hook in string else None. If not a valid event is given,
            this returns None.
        """
        if event not in self._hooks:
            return None
        return self._hooks[event]

    def remove_connect_hook(self, event):
        """
        Remove hook which is set in given event if exists.

        This method removes all information of signals and slots connected to given
        event as well as hook. If hook of given event does not exist, this raises
        a KeyError.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.EVENTS.
        """
        del self._hooks[event]
        del self._signals[event]
        del self._slots[event]
        del self._indices[event]

    def get_hook_index(self, event):
        """
        Returns index of hook in method arguments

        :param event: str
        :return: int
        """
        if event in self._indices:
            return self._indices[event]
        return None

    @staticmethod
    def map(ehandler):
        """
        Decorator method to call slot method when event connected to slot has been called.

        When event has been called, this decorator method is called with event method as arg,
        'ehandler'. Then wrapper function wraps the event and will be executed.

        Inside the wrapper, it takes all args from the event. The First arg is 'self' which is
        an instance of Kiwoom class. The rest of args depends on which event has been called.

        Firstly, execute event handler which is initially an empty method in the module. But
        this process is needed for when an empty default method is overridden. Then, find the
        right slot connected to the event. If found, execute it with the same args forwarded
        from event. If not, just print a warning message. This message can be turned on/off.

        Usage example
        >>  class Kiwoom(API):
        >>      ...
        >>      @map  # decorator
        >>      def on_event_connect(self, err_code):
        >>          pass  # empty event
        >>      ...

        :param ehandler: method
            One of pre-defined event handlers, see kiwoom.config.EVENTS.
        :return: function
            Wrapper function that executes a slot method connected to the event.
        """
        @wraps(ehandler)  # keep docstring of event handler
        def wrapper(api, *args):
            # Variables
            event = getattr(ehandler, '__name__')
            idx = api.get_hook_index(event)
            hook = api.get_connect_hook(event)
            args = args[:Connector.nargs[event]]

            # To execute the default event handler in case of overriding
            ehandler(api, *args)

            # To find connected slot
            try:
                # If hook is set on the event, then key becomes arg that corresponds to the hook
                # ex) if hook is rq_name for on_receive_tr_data, then key becomes arg passed into rq_name
                key = args[idx] if hook else None
                # To retrieve the right slot
                slot = api.slot(event, key)

            except KeyError:
                if not config.MUTE:
                    msg = dedent(
                        f"""
                        kiwoom.{event}({', '.join(map(str, args))}) has been called.
    
                        But the event handler, '{event}', is not connected to any slot.
                        Please try to connect event and slot by using kiwoom.connect() method.
                          >> api.connect('{event}', slot=slot_method)
    
                        This warning message can disappear by the following. 
                          >> kiwoom.config.MUTE = True  # global variable
                        """
                    )
                    print(msg)
                # To prevent executing slot that does not exist, just return
                return

            # Execute the connected slot
            slot(*args)

        # Return wrapper function to decorate
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
        config.MUTE = bool

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
