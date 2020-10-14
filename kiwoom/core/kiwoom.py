from kiwoom.wrapper.api import API
from kiwoom.config.general import event_handlers
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
        Decorator @Connector uses this information

        Possible Combinations:
        1) signal, slot
            Connects signal and slot by its method name as a key
            ex) self.connect(signal.balance, slot.balance)
                >> Please refer to the sample code below

                api = Kiwoom()
                signal, slot = Signal(api), Slot(api)
                signal.balance()  # send request for balance data
                print(slot.data)  # check received data from server

                class Signal:
                    def __init__(self, api):
                        self.api = api

                    def balance(self, prev_next='0'):
                        tr_code = 'opw00018':  # 계좌평가잔고내역요청
                        inputs = dict{
                            '계좌번호': 'xxxxxxxx',
                            '비밀번호': 'xxxx',
                            '비밀번호입력매체구분': '00',
                            '조회구분': '1'
                        }
                        for key, val in inputs.items():
                            self.api.set_input_value(key, val)

                        # NOTICE HERE : rq_name='balance'
                        self.api.comm_rq_data(rq_name='balance', tr_code, prev_next, scr_no='xxxx')
                        self.api.loop()  # prevent executing further before completion of downloading

                class Slot:
                    def __init__(self, api):
                        self.api = api
                        self.data = defaultdict(list)
                        self.is_downloading = False

                    def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):
                        # To initiate downloading and saving data
                        if not self.is_downloading:
                            self.data = defaultdict(list)
                            self.is_downloading = True

                        # To fetch multi data and save
                        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
                        for i in range(cnt):
                            for key in ['종목번호', '종목명', '평가손익', ...]:
                                self.data[key].append(
                                    str.strip(  # or int(), float()
                                        self.api.get_comm_data(tr_code, rq_name, i, key)
                                    )
                                )

                        # NOTICE HERE : key='balance'
                        if prev_next == '2':
                            fn = self.api.signal('balance')  # or self.api.signal(rq_name)
                            fn(prev_next)  # call signal function again to receive remaining data

                        else:
                            # To fetch single data
                            for key in ['총평가손익금액', '총수익률(%)']:
                                self.data[key].append(
                                    float(self.api.get_comm_data(tr_code, rq_name, 0, key)
                                )

                            # Downloading completed
                            self.is_downloading = False
                            self.api.unloop()

                class Kiwoom:  # already implemented in library
                    ...
                    @Connector(key='rq_name')  # already implemented in library
                    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
                        # NOTICE HERE
                        #   if 'balance' is given to 'rq_name', Connector(key='rq_name') automatically
                        #   forwards args to slot.balance(scr_no, 'balance', tr_code, record_name, prev_next)
                        pass

        2) signal, slot, key
            Connects signal and slot by given key
            ex) self.connect(signal.balance, slot.balance, 'xxxx')
                >> Please refer to the sample code below
                >> Note that usage for this combination highly depends on implementor
                >> Below is just a sample and not a recommended way for usage

                # Signal - Almost same with the above code but rq_name
                def balance(prev_next='0'):
                    ...
                    self.api.comm_rq_data(rq_name='xxxx', tr_code, prev_next, scr_no='xxxx')
                    self.api.loop()

                # Slot - Almost same with the above code but rq_name
                def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):  # Slot
                    ...
                    if prev_next == '2':
                        fn = self.api.signal('xxxx')  # or self.api.signal(rq_name)
                        fn(prev_next)  # call signal function again to receive remaining data
                    ...

                # Kiwoom - Already implemented in library
                @Connector(key='rq_name')
                def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
                    # NOTICE HERE
                    #   if 'xxxx' is given to 'rq_name', Connector(key='rq_name') automatically
                    #   forwards args to slot.balance(scr_no, 'xxxx', tr_code, record_name, prev_next)
                    pass

        3) slot, event
            Connects slot to one of pre-defined 8 events  # print(kiwoom.event_handlers)
            ex) self.connect(slot.message, 'on_receive_msg')
                >> Please refer to the sample code below
                >> Note that default slot for on_receive_msg is already set in library.

                # Slot
                def message(scr_no, rq_name, tr_code, msg):
                    logger.log(scr_no, rq_name, tr_code, msg)

                # Kiwoom - Already implemented in library
                @Connector()
                def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
                    # NOTICE HERE
                    #   if on_receive_msg is called, then Connector automatically
                    #   forwards args to slot.message(scr_no, rq_name, tr_code, msg)
                    pass
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
        """

        :param key:
        :return:
        """
        return self._signals[key]

    def slot(self, key):
        """

        :param key:
        :return:
        """
        return self._slots[key]

    def login(self):
        self.api.comm_connect()
        self.api.loop()

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
