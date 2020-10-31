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

    """
    def __init__(self):
        super().__init__()
        self.msg = True
        self._qloop = QEventLoop()

        # To connect signals and slots
        # >> dic[event][key] returns signal/slot method
        self._signals = defaultdict(dict)
        self._slots = defaultdict(dict)
        self._hooks = dict()

        # To solve conflict between PyQt and input()
        # pyqtRemoveInputHook()

        # To solve the issue that IDE hides error traceback
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook

        # To set hooks for each event
        self.set_connect_hook('on_receive_tr_data', arg='rq_name')
        self.set_connect_hook('on_receive_tr_condition', arg='condition_name')
        self.set_connect_hook('on_receive_real_condition', arg='condition_name')

        # To connect default slots to basic two event handlers
        self.connect('on_event_connect', slot=self.__on_event_connect_slot)
        self.connect('on_receive_msg', slot=self.__on_receive_msg_slot)

    def loop(self):
        if not self._qloop.isRunning():
            self._qloop.exec()

    def unloop(self):
        if self._qloop.isRunning():
            self._qloop.exit()

    def login(self):
        self.comm_connect()
        self.loop()

    def message(self, bool):
        """
        :param bool: True / False to print message from kiwoom.on_receive_msg()
        """
        self.msg = bool

    def signal(self, event, key=None):
        """
        :param event: string of event
        :param key: string of key (method name by default)
        :return: signal method
        """
        if self.get_connect_hook(event) is None:
            return self._signals[event]
        return self._signals[event][key]

    def slot(self, event, key=None):
        """
        :param event: string of event
        :param key: string of key (method name by default)
        :return: slot method
        """
        if self.get_connect_hook(event) is None:
            return self._slots[event]
        return self._slots[event][key]

    def connect(self, event, signal=None, slot=None, key=None):
        """
        Recommended : Function name will be same

        A method that maps events to slots.
        self._slots[event] = slot

        Decorator @Connector uses this information.

        :param signal: a method that requests to the server
        :param slot: a method that reacts the server's response
        :param event: string of event handler name
        :param key: string to be used for rq_name from on_receive_tr_data
        """
        valid = False
        connectable = Connector.connectable

        if not is_valid_event(event):
            return

        # Directly connect slot to the event
        if self.get_connect_hook(event) is None:
            # Key can't be used here
            if key is not None:
                pass

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

    def get_connect_hook(self, event):
        """
        :param event:
        :param arg:
        :return:
        """
        if event not in self._hooks:
            return None
        return self._hooks[event]

    def set_connect_hook(self, event, param):
        """

        :param event:
        :param param:
        :return:
        """
        if not is_valid_event(event):
            return
        # To check given arg is valid
        args = self.api_arg_spec(event)
        if param not in args:
            raise KeyError(f"{param} is not valid.\nSelect one of {args}.")
        # Set connect hook
        self._hooks[event] = param

    def remove_connect_hook(self, event):
        del self._hooks[event]

    def api_arg_spec(self, fn):
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
    Methods that return error codes
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
