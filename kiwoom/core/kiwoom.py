from kiwoom.wrapper.api import API, event_handlers
from kiwoom.config.error import err_msg, catch_error
from kiwoom.core.connector import Connector

from PyQt5.QtCore import QEventLoop
from PyQt5.QtCore import pyqtRemoveInputHook

import sys


class Kiwoom(API):
    def __init__(self):
        super().__init__()
        self.msg = True
        self.qloop = QEventLoop()

        # To connect signals and slots
        self._signals = dict()
        self._slots = dict()

        # To solve conflict between PyQt and input()
        pyqtRemoveInputHook()

        # To solve the issue that IDE hides error traceback
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook

        # To connect default slots to the most basic two event handlers
        self.connect(slot=self.__on_event_connect_slot, event='on_event_connect')
        self.connect(slot=self.__on_receive_msg_slot, event='on_receive_msg')

    def loop(self):
        if not self.qloop.isRunning():
            self.qloop.exec()

    def unloop(self):
        if self.qloop.isRunning():
            self.qloop.exit()

    def message(self, bool):
        """
        :param bool: True / False to print message from kiwoom.on_receive_msg()
        """
        self.msg = bool

    def connect(self, signal=None, slot=None, event=None, key=None):
        """
        :param signal: a method that requests to the server
        :param slot: a method that reacts the server's response
        :param event: string of event handler name
        :param key: string

        A method that connects signal and slot
        Decorator @Connector uses this info

        possible combinations:
        1) signal, slot
            connects signal and slot by its method name as a key
            ex) self.connect(signal.balance, slot.balance)
                >>
                def signal.balance():
                    tr_code = 'opw00018':  # 계좌평가잔고내역요청
                    inputs = dict{
                        '계좌번호': 'xxxxxxxx',
                        '비밀번호': 'xxxx',
                        '비밀번호입력매체구분': '00',
                        '조회구분': '1'
                    }
                    for key, val in inputs.items():
                        self.api.set_input_value(key, val)

                    self.api.comm_rq_data('balance', tr_code, '0', 'xxxx')
                    self.api.loop()

                def slot.balance(self, scr_no, rq_name, tr_code, record_name, prev_next):






                 --> on_receive_tr_data(rq_name='balance') --> slot.balance()

        2) signal, slot, key
            connects signal and slot by given key
            ex) signal.tick() --> on_receive_tr_data(rq_name='history') --> slot.balance()

        3) slot, event
            connects slot to event
        """
        valid = False
        connectable = Connector.connectable

        # Connect signal and slot with/without key
        if connectable(signal):
            if connectable(slot):
                valid = True
                if key is None:
                    self._signals[getattr(slot, '__name__')] = signal
                    self._slots[getattr(signal, '__name__')] = slot
                else:
                    self._signals[key] = signal
                    self._slots[key] = slot

        # Connect slot and event
        elif connectable(slot):
            if event is not None:
                if event not in event_handlers:
                    raise KeyError(f"{event} is not a valid event handler.\nSelect one of {event_handlers}.")
                valid = True
                self._slots[event] = slot

        # Nothing is connected
        if not valid:
            raise RuntimeError(f"Unsupported combination of inputs. Please read below.\n\n{self.connect.__doc__}")

    def signal(self, key):
        return self._signals[key]

    def slot(self, key):
        return self._slots[key]

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

    @Connector(key='rq_name')
    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
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
    def on_receive_tr_condition(self, scr_no, code_list, cond_name, index, next):
        pass

    @Connector()
    def on_receive_real_condition(self, code, type, cond_name, cond_index):
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
            self, rq_name, scr_no,
            acc_no, order_type, code,
            qty, price, hoga_gb,
            credit_gb, loan_date, org_order_no
    ):
        return super().send_order_credit(
            rq_name, scr_no, acc_no,
            order_type, code, qty,
            price, hoga_gb, credit_gb,
            loan_date, org_order_no
        )

    @catch_error
    def set_real_reg(self, scr_no, code_list, fid_list, opt_type):
        return super().set_real_reg(scr_no, code_list, fid_list, opt_type)

    # Default event slot for on_event_connect
    def __on_event_connect_slot(self, err_code):
        print(f'\n로그인 {err_msg(err_code)}')
        print(f'\n* 시스템 점검\n  - 월 ~ 토 : 05:05 ~ 05:10\n  - 일 : 04:00 ~ 04:30\n')
        self.unloop()

    # Default event slot for on_receive_msg_slot
    def __on_receive_msg_slot(self, scr_no, rq_name, tr_code, msg):
        if self.msg:
            print(f'\n화면번호: {scr_no}, 요청이름: {rq_name}, TR코드: {tr_code} \n{msg}\n')
