from kiwoom.wrapper.api import API
from kiwoom.config.error import catch_error
from kiwoom.core.signal import Signal
from kiwoom.core.slot import Slot
from kiwoom.core.connector import Connector

from inspect import getfullargspec
from PyQt5.QtCore import QEventLoop

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
        signal and slot by default. See examples on the tutorials link below.
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
    # Class variable just for convenience
    map = Connector.map

    def __init__(self):
        super().__init__()
        self.msg = True
        self._qloop = QEventLoop()

        # To solve the issue that IDE hides error traceback
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook

        # To connect signals and slots
        self._connector = Connector()
        self._signal = Signal(self)
        self._slot = Slot(self)

        # To set hooks for each event
        self.set_connect_hook('on_receive_tr_data', param='rq_name')
        self.set_connect_hook('on_receive_tr_condition', param='condition_name')
        self.set_connect_hook('on_receive_real_condition', param='condition_name')

        # To connect default slots to basic two events
        self.connect('on_event_connect', slot=self._slot.on_event_connect)
        self.connect('on_receive_msg', slot=self._slot.on_receive_msg)

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
        return self._connector.signal(event, key)

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
        return self._connector.slot(event, key)

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
        self._connector.connect(event, signal=signal, slot=slot, key=key)

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

        The Convention is that the names of signal and slot that deal with the related task
        are recommended to be the same, so that 'key' is set to be the method name of
        signal and slot by default. See examples on the tutorials link below.
        https://github.com/breadum/kiwoom/blob/main/tutorials/4.%20TR%20Data.py

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        :param param: str
            Parameter name defined in given event. To see all parameters to event,
            use Kiwoom.api_arg_spec(event) method or help(...) built-in function.
        """
        self._connector.set_connect_hook(event, param)

    def get_connect_hook(self, event):
        """
        Returns a hook (i.e. name of parameter) set in given event.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        :return: str or None
            If exists, returns hook in string else None. If not a valid event is given,
            this returns None.
        """
        return self._connector.get_connect_hook(event)

    def remove_connect_hook(self, event):
        """
        Remove hook which is set in given event if exists.

        This method removes all information of signals and slots connected to given
        event as well as hook. If hook of given event does not exist, this raises
        a KeyError.

        :param event: str
            One of the pre-defined event names in string. See kiwoom.config.events.
        """
        self._connector.remove_connect_hook(event)

    @staticmethod
    def api_arg_spec(fn):
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
    @map
    def on_event_connect(self, err_code):
        pass

    @map
    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        pass

    @map
    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next, *args):
        pass

    @map
    def on_receive_real_data(self, code, real_type, real_data):
        pass

    @map
    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        pass

    @map
    def on_receive_condition_ver(self, ret, msg):
        pass

    @map
    def on_receive_tr_condition(self, scr_no, code_list, condition_name, index, next):
        pass

    @map
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
