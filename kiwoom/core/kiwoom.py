from kiwoom.wrapper.api import API, event_handlers
from kiwoom.config.error import err_msg
from kiwoom.core.connector import Connector

from textwrap import dedent
from PyQt5.QtCore import QEventLoop
from PyQt5.QtCore import pyqtRemoveInputHook
from inspect import ismethod, isfunction, isclass, ismodule, getattr_static

import sys


class Kiwoom(API):

    def __init__(self, bot=None):
        super().__init__()
        self.msg = True
        self.qloop = QEventLoop()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        # To connect signals and slots
        self._signals = dict()
        self._slots = dict()

        # To solve conflict between PyQt and input()
        pyqtRemoveInputHook()

        # To solve the issue that IDE hides error traceback
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook

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
        :param event: the name of event handler
        :param signal: a bound method (i.e. instance method)
        :param slot: a bound method (i.e. instance method)
        :param key: string

        Manually connect signal to slot or signal with rq_name to the given slot.
        Use this function when a method's name is different in signal and slot.
        """
        # For convenience
        connectable = Connector.connectable

        # Connect signal and slot with/without key
        if signal is not None and connectable(signal):
            if slot is not None and connectable(slot):
                key = key if key is not None else getattr
                if key is None:
                    self._signals[getattr(slot, '__name__')] = signal
                    self._slots[getattr(signal, '__name__')] = slot
                else:
                    self._signals[key] = signal
                    self._slots[key] = slot

            elif event is not None:
                raise RuntimeError(f"Event, {event}, should be connected to slot, not signal.")

        # Connect slot and event
        elif slot is not None and connectable(slot):
            if event is not None:
                if event not in event_handlers:
                    raise KeyError(f"{event} is not a valid event handler.\nSelect one of {event_handlers}.")
                self._slots[event] = slot

        # Unsupported combination of inputs
        else:
            raise RuntimeError(f"Unsupported combination of inputs. Please read below.\n\n{help(self.connect)}")

    def signal(self, key):
        return self._signals[key]

    def slot(self, key):
        return self._slots[key]

    # Event Handlers
    @Connector()
    def on_event_connect(self, err_code):
        print(f'\n로그인 {err_msg(err_code)}')
        print(f'\n* 시스템 점검\n  - 월 ~ 토 : 05:05 ~ 05:10\n  - 일 : 04:00 ~ 04:30\n')

    @Connector()
    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        if self.msg:
            print(f'\n화면번호: {scr_no}, 요청이름: {rq_name}, TR코드: {tr_code} \n{msg}\n')

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