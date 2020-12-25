from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from kiwoom.utils import clock
from functools import wraps

import sys


def timer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Extract bot instance
        bot = args[0]

        def unloop():
            if not bot.connected():
                print('Timeover for login. Please try again.')
                bot.api.unloop()

        # Set timer waiting for 1 minute
        timer = QTimer(bot.api)
        timer.singleShot(60 * 1000, unloop)

        # Execute signal function
        fn(*args, **kwargs)

    return wrapper


class Downloader:
    # Variable to trace download status
    nrq = 0

    # Decorates Signal.histories()
    @staticmethod
    def watcher(fn):
        # To keep docstring of fn
        @wraps(fn)
        # Define a wrapper
        def wrapper(*args, **kwargs):
            # Extract bot instance
            signal = args[0]
            Downloader.nrq = 0

            # If not connected, exit program.
            if not signal.connected():
                return sys.exit(0)

            # Slot function to be called AFTER 10 min
            def watcher():
                # Number of request to server
                nrq = signal.share.get_single('histories', 'nrq')

                # If disconnected or froze by some issue, exit program
                if not signal.connected() or nrq == Downloader.nrq:
                    # Close all pop-up windows from Kiwoom
                    app = QApplication.instance()
                    app.closeAllWindows()

                    # Set reboot param and unloop
                    signal.share.update_single('history', 'reboot', True)
                    signal.api.unloop()

                    # Exit script after 60 seconds
                    print(f'Downloader stopped at {clock()}. Exit script.')
                    return QTimer(app).singleShot(60, sys.exit)

                # Update nrq
                Downloader.nrq = nrq

            # Set timer for every 10 minutes
            timer = QTimer(signal.api)
            timer.start(10 * 60 * 1000)
            timer.timeout.connect(watcher)

            # Execute Slot.on_event_connect()
            return fn(*args, **kwargs)

        # Returns defined wrapper
        return wrapper

    # Decorates Slot.history()
    @staticmethod
    def handler(fn):
        # To keep docstring of fn
        @wraps(fn)
        # Define wrapper function
        def wrapper(*args, **kwargs):
            slot = args[0]
            code = slot.share.get_args('history', 'code')

            """
            # Check server reboot time
            if not server_available():
                # Print error message
                print(f'Server reboots soon. Stop downloading at {code}.')
                # Set reboot parameter True
                slot.share.update_single('history', 'reboot', True)
                # Return to Signal.history()
                return slot.api.unloop()
            """

            # Execute Slot.history(*args)
            try:
                fn(*args, **kwargs)

            # Handle RuntimeError caused by not monotonic increasing data
            except RuntimeError as err:
                # Print error message
                print(f'\nAn error occurred at Slot.history(code={code}, ...).\n{err}\n')
                # Reset variables
                slot.share.remove_history(code)
                # Return to Signal.history()
                slot.api.unloop()

        # Returns defined wrapper
        return wrapper
