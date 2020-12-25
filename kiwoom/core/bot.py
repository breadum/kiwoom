from kiwoom.core.kiwoom import Kiwoom
from kiwoom.core.signal import Signal
from kiwoom.core.slot import Slot
from kiwoom.data import Share
from kiwoom.config.screen import Screen
from kiwoom.utils import effective_args

from PyQt5.QtWidgets import QApplication
from functools import wraps


class Bot:
    def __init__(self, signal=None, slot=None):
        self.api = Kiwoom()
        self.scr = Screen()
        self.share = Share()

        # Signal and Slot instance
        self.signal = signal if signal else Signal(self.api)
        self.slot = slot if slot else Slot(self.api)

        # Initiate instance with variables
        self.signal.init(api=self.api, scr=self.scr, share=self.share)
        self.slot.init(api=self.api, scr=self.scr, share=self.share)

        # Default setting for basic events
        try:
            self.api.connect('on_event_connect', signal=self.signal.login, slot=self.slot.on_event_connect)
            self.api.connect('on_receive_msg', slot=self.slot.on_receive_msg)
        except AttributeError:
            pass

        # Default setting for on_receive_tr_data event
        self.api.set_connect_hook('on_receive_tr_data', 'rq_name')
        self.api.connect('on_receive_tr_data', self.signal.history, self.slot.history)

    @wraps(Signal.histories)
    def histories(
            self,
            market=None,
            sector=None,
            period=None,
            unit=None,
            start=None,
            end=None,
            slice=None,
            code=None,
            path=None,
            merge=False,
            warning=True
    ):
        self.signal.histories(**effective_args(locals()))

    def exit(self, rcode):
        """
        Close all windows open adn exit the application that runs this bot

        :param rcode: int
            return code when exiting the program
        """
        app = QApplication.instance()
        app.closeAllWindows()
        app.exit(rcode)
