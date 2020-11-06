from kiwoom.wrapper.api import API
from kiwoom.config import is_valid_event
from kiwoom.config.error import msg, catch_error
from kiwoom.core.connector import Connector

from inspect import getfullargspec
from collections import defaultdict
from PyQt5.QtCore import QEventLoop
# from PyQt5.QtCore import pyqtRemoveInputHook

import sys


class Kiwoom(API):
    """
    Main class that can make use of Kiwoom Open API+

    This class wraps all API methods described in KOA studio and Open API+ Manual Guide.
    All methods are wrapped in dynamicCall from PyQt5. Methods and variables names are
    all converted into pythonic way convention, OnReceiveTrData -> on_receive_tr_data.

    Some of extra functions other than pure API are as follows.
    1) Kiwoom.loop() & Kiwoom.unloop()
        These methods are used to prevent from executing codes before data requested
        has not been received yet. Normally, loop can be used in signal methods to stop
        executing further and unloop can be used in slot methods to executing codes that
        are waiting in the signal methods.

    2) Kiwoom.connect(event, signal, slot)
        This method connects signals and slots to one of pre-defined events. Information
        saved in this method is used by decorator @Connector() which wraps the events.

    3) Kiwoom.set_connect_hook(event, param)
        When an event needs multiple slots to connect, depending on specific tasks, set
        a hook(key) to select which slot to map. The hook must be one of the parameters
        in the definition of the event method. Parameters can be found by help built-in
        function or Kiwoom.api_arg_spec(event).

        If hook is set to the given parameter, argument passed into the parameter when
        the event is called, is going to be a key to connect event, signal and slot.

        Convention is that the name of signal and slot that deal with the related task
        is recommended to be the same, so that 'key' is set to be the method name of
        signal and slot by default. See examples on the tutorial link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/4.%20TR%20Data.py

        Kiwoom.get_connect_hook(), Kiwoom.remove_connect_hook() are also available.

    4) Kiwoom.signal(event, key=None) & Kiwoom.slot(event, key=None)
        If signal and slot are connected to specific event, then these methods return
        the connected signal or slot method respectively. 'key' is needed when hook is
        set by Kiwoom.set_connect_hook().

        When requesting data to server is needed, specifically if more data is available,
        Kiwoom.signal() returns the exact signal method that can request more data.

        When an event is called, Kiwoom.slot() returns the exact slot method that can
        handle data received from the event. This method is used in Connector decorator
        that wraps events to execute connected slot with the event.

    5) @Connector()
        Decorator class that forwards args received from called event into connected slot.
        This class wraps all pre-defined events, and automatically calls connected slots.
    """
    def __init__(self):
        super().__init__()
        self.msg = True
        self._qloop = QEventLoop()

        # To connect signals and slots
        # >> If no hook is set, dic[event] returns signal/slot.
        # >> If hook is set, dic[event][key] returns signal/slot.
        self._signals = dict()
        self._slots = dict()
        self._hooks = dict()

        # To solve conflict between PyQt and input()
        # pyqtRemoveInputHook()

        # To solve the issue that IDE hides error traceback
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook

        # To set hooks for each event
        self.set_connect_hook('on_receive_tr_data', param='rq_name')
        self.set_connect_hook('on_receive_tr_condition', param='condition_name')
        self.set_connect_hook('on_receive_real_condition', param='condition_name')

        # To connect default slots to basic two events
        self.connect('on_event_connect', slot=self.__on_event_connect_slot)
        self.connect('on_receive_msg', slot=self.__on_receive_msg_slot)

    def loop(self):
        """
        Stop executing codes by running QEventLoop in PyQt5

        If loop is already running, then this does nothing, else freezing. This
        method can be used in signal methods to wait response from the server.
        """
        if not self._qloop.isRunning():
            self._qloop.exec()

    def unloop(self):
        """
        Keep executing codes that are blocked by Kiwoom.loop().

        If loop is not running, then this does nothing, else unfreezing. This
        method can be used in slot methods to execute awaiting codes. If the
        slot methods called, then it means client received response from server.
        There is no need to block codes that are awaiting response, anymore.
        """
        if self._qloop.isRunning():
            self._qloop.exit()

    def login(self):
        """
        Request login to the server by CommConnect API method.

        See '개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect' in KOA Studio.
        """
        self.comm_connect()
        self.loop()

    def message(self, bool):
        """
        Turn on/off printing message from Kiwoom.on_receive_msg() event.

        :param bool: bool
            If True, then it prints message else does not.
        """
        self.msg = bool

    def signal(self, event, key=None):
        """
        Returns signal methods connected to the event.

        If signal and slot are connected to specific event by Kiwoom.connect() method,
        then this method returns the connected signal method. If signal is not connected,
        or wrong key is given, this raises a KeyError.

        'key' is needed when hook is set by Kiwoom.set_connect_hook(). 'key' is set to
        be the name of signal method by default unless another string is set on purpose
        when connecting.

        When requesting data to server is needed, specifically if more data is available,
        Kiwoom.signal() returns the exact signal method that can request more data.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        :param key: str, optional
            If hook is set by Kiwoom.set_connect_hook() method and signal is connected
            by Kiwoom.connect(), then key is needed. 'key' is set to be name of the
            signal method by default unless another 'key' is given when connecting.
        :return: method
            Signal method connected to the given event. If wrong event, returns None.
        """
        if not is_valid_event(event):
            return None
        if self.get_connect_hook(event) is None:
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
            One of the pre-defined event names in string. See kiwoom.config.events.
        :param key: str, optional
            If hook is set by Kiwoom.set_connect_hook() method and slot is connected
            by Kiwoom.connect(), then key is needed. 'key' is set to be name of the
            slot method by default unless another 'key' is given when connecting.
        :return: method or None
            Slot method connected to the given event. If wrong event, returns None.
        """
        if not is_valid_event(event):
            return None
        if self.get_connect_hook(event) is None:
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

        Please see tutorial example on the link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/4.%20TR%20Data.py

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
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

        if not is_valid_event(event):
            return

        # Directly connect slot to the event
        if self.get_connect_hook(event) is None:
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

        # Connect slot to the event when
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
        signal and slot by default. See examples on the tutorial link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/4.%20TR%20Data.py

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        :param param: str
            Parameter name defined in given event. To see all parameters to event,
            use Kiwoom.api_arg_spec(event) method or help(...) built-in function.
        """
        if not is_valid_event(event):
            return
        # To check given arg is valid
        args = self.api_arg_spec(event)
        if param not in args:
            raise KeyError(f"{param} is not valid.\nSelect one of {args}.")
        # To set connect hook for event
        self._hooks[event] = param
        # Initialize structure to get signal/slot method by dic[event][key]
        self._signals[event] = dict()
        self._slots[event] = dict()

    def get_connect_hook(self, event):
        """
        Returns a hook (i.e. name of parameter) set in given event.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        :return: str or None
            If exists, returns hook in string else None. If not a valid event is given,
            this returns None.
        """
        if not is_valid_event(event):
            return None
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
            One of the pre-defined event names in string. See kiwoom.config.events.
        """
        del self._hooks[event]
        del self._signals[event]
        del self._slots[event]

    def api_arg_spec(self, fn):
        """
        Returns a string list of parameters to given API function

        :param fn: str
            Name of API function to get list of parameters.
        :return: list
            Parameters of given API function in list of strings.
        """
        args = getfullargspec(getattr(API, fn)).args
        return args

    """
    Event Handlers (8)
        on_event_connect
        on_receive_msg
        on_receive_tr_data
        on_receive_real_data
        on_receive_chejan_data
        on_receive_condition_ver
        on_receive_tr_condition
        on_receive_real_condition
    """
    @Connector()
    def on_event_connect(self, err_code):
        pass

    @Connector()
    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        pass

    @Connector()
    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next, *args):
        pass

    @Connector()
    def on_receive_real_data(self, code, real_type, real_data):
        pass

    @Connector()
    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        pass

    @Connector()
    def on_receive_condition_ver(self, ret, msg):
        pass

    @Connector()
    def on_receive_tr_condition(self, scr_no, code_list, condition_name, index, next):
        pass

    @Connector()
    def on_receive_real_condition(self, code, type, condition_name, condition_index):
        pass

    """
    Methods that return error codes.
        comm_rq_data
        comm_kw_rq_data
        send_order
        send_order_credit
        set_real_reg
    """
    @catch_error
    def comm_rq_data(self, rq_name, tr_code, prev_next, scr_no):
        return super().comm_rq_data(rq_name, tr_code, prev_next, scr_no)

    @catch_error
    def comm_kw_rq_data(self, arr_code, next, code_cnt, type_flag, rq_name, scr_no):
        return super().comm_rq_data(arr_code, next, code_cnt, type_flag, rq_name, scr_no)

    @catch_error
    def send_order(self, rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no):
        return super().send_order(rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no)

    @catch_error
    def send_order_credit(
            self,
            rq_name,
            scr_no,
            acc_no,
            order_type,
            code,
            qty,
            price,
            hoga_gb,
            credit_gb,
            loan_date,
            org_order_no
    ):
        return super().send_order_credit(
            rq_name,
            scr_no,
            acc_no,
            order_type,
            code,
            qty,
            price,
            hoga_gb,
            credit_gb,
            loan_date,
            org_order_no
        )

    @catch_error
    def set_real_reg(self, scr_no, code_list, fid_list, opt_type):
        return super().set_real_reg(scr_no, code_list, fid_list, opt_type)

    """
    Default slots to the most basic two events.
        on_event_connect
        on_receive_msg
    """
    # Default event slot for on_event_connect
    def __on_event_connect_slot(self, err_code):
        """
        Default slot for 'on_event_connect'

        When on_event_connect is called, this method automatically will be called.
        """
        print(f'\n로그인 {msg(err_code)}')
        print(f'\n* 시스템 점검\n  - 월 ~ 토 : 05:05 ~ 05:10\n  - 일 : 04:00 ~ 04:30\n')
        self.unloop()

    # Default event slot for on_receive_msg_slot
    def __on_receive_msg_slot(self, scr_no, rq_name, tr_code, msg):
        """
        Default slot for 'on_receive_msg'

        Whenever the server sends a message, this method prints depending on below.
        >> Kiwoom.message(True)
        >> Kiwoom.message(False)
        """
        if self.msg:
            print(f'\n화면번호: {scr_no}, 요청이름: {rq_name}, TR코드: {tr_code} \n{msg}\n')
