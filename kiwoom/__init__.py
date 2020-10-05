import sys
# sys.path.append('C:\\Users\\Bread Um\\PycharmProjects\\OpenAPI')

from PyQt5.QtWidgets import QApplication

from kiwoom.config.error import err_msg, catch_error
from kiwoom.core.kiwoom import Kiwoom
from kiwoom.wrapper.api import API

import kiwoom

if __name__ == '__main__':

    app = QApplication(sys.argv)

    api = Kiwoom()

    class Signal():
        def __init__(self, api):
            self.api = api

        def login(self):
            self.api.comm_connect()
            self.api.loop()

    class Slot():
        def __init__(self, api):
            self.api = api

        def on_event_connect(self, err_code):
            print(f'로그인 {kiwoom.err_msg(err_code)}')
            self.api.unloop()

    # Initialize
    signal = Signal(api)
    slot = Slot(api)

    # Connect slot to the target event handler
    api.connect(slot=slot.on_event_connect, event='on_event_connect')

    # Send login signal to the server
    signal.login()

    help(api.comm_connect)
    help(api.on_receive_msg)

    app.exec()
