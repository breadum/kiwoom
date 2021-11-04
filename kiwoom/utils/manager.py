import sys
from functools import wraps
from traceback import format_exc

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from kiwoom.utils.general import clock


def timer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Extract bot instance
        bot = args[0]

        def unloop():
            if not bot.connected():
                print(f'[{clock()}] Timeover for login. Please try again.')
                # Close all pop-up windows from Kiwoom
                app = QApplication.instance()
                app.closeAllWindows()
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
            bot = args[0]
            Downloader.nrq = 0

            # If not connected, exit program.
            if not bot.connected():
                return sys.exit(0)

            # Slot function to be called AFTER 10 min
            def watcher():
                # Number of request to server
                nrq = bot.share.get_single('histories', 'nrq')

                # If disconnected or froze by some issue, exit program
                if not bot.connected() or nrq == Downloader.nrq:
                    # Close all pop-up windows from Kiwoom
                    app = QApplication.instance()
                    app.closeAllWindows()

                    # Set restart param and unloop
                    bot.share.update_single('history', 'restart', True)
                    bot.api.unloop()

                    # Exit script after 60 seconds
                    print(f'\n[{clock()}] As downloader has frozen, exiting the program in 60 sec.')
                    return QTimer(app).singleShot(60, sys.exit)

                # Update nrq
                Downloader.nrq = nrq

            # Set timer for every 10 minutes
            timer = QTimer(bot.api)
            timer.start(10 * 60 * 1000)
            timer.timeout.connect(watcher)

            # Execute Slot.on_event_connect()
            return fn(*args, **kwargs)

        # Returns defined wrapper
        return wrapper

    # Decorates Server.history()
    @staticmethod
    def handler(fn):
        # To keep docstring of fn
        @wraps(fn)
        # Define wrapper function
        def wrapper(*args):
            server = args[0]
            code = server.share.get_args('history', 'code')

            # Execute Server.history(*args)
            try:
                fn(*args)

            # RuntimeError can be caused by two cases
            # 1) not monotonic increasing data
            # 2) received wrong data other than requested
            except Exception:
                # Print error message
                print(f'\n[{clock()}] An error at Server.history{args[1:]} with code={code}.\n\n{format_exc()}')
                # Reset variables
                server.share.remove_history(code)
                server.share.remove_args('history')
                server.share.update_single('history', 'error', True)
                # Return to Signal.history()
                server.api.unloop()

        # Returns defined wrapper
        return wrapper
