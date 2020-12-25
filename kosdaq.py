import time
import sys

from kiwoom.config.error import ExitCode
from kiwoom.utils import clock
from kiwoom.core.bot import Bot
from kiwoom.core import Connector

from multiprocessing import Process, Manager
from PyQt5.QtWidgets import QApplication


def download(kwargs, share):
    # Initialize and login
    app = QApplication(sys.argv)
    umbot = Bot()
    umbot.signal.login()

    # Download start
    result = umbot.histories(**kwargs)

    # Update result
    if result == ExitCode.success:
        share['done'] = True
        share['success'] = True

    elif result == ExitCode.failure:
        share['error'] = True
        share['success'] = False

    else:
        share['slice'] = result
        share['success'] = True

    # Exit
    time.sleep(1)
    umbot.exit()


def update_kwargs(kwargs, slice):
    if 'code' in kwargs:
        del kwargs['code']
    kwargs['slice'] = slice
    return kwargs


# KOSDAQ Done till 1218
if __name__ == '__main__':
    Connector.mute(True)

    # Options
    options = ['start', 'end', 'slice']

    # Default args
    period = 'min'
    kwargs = {
        'sector': '0',
        'period': period,
        'path': 'E:/Data/sector/KOSPI/' + period,
        'merge': True,
        'warning': False,
    }

    # Variables to set
    ntry, maxtry = 0, 3
    share = Manager().dict()
    share['done'] = False
    share['error'] = False
    share['success'] = False

    # Loop start
    while True:
        # Print time
        print(f"Start new loop at {clock()}")

        # Variables
        share['error'] = False
        share['success'] = False

        # Spawning a process
        p = Process(target=download, args=(kwargs, share), daemon=True)
        p.start()
        p.join()

        # 1) Download done
        if share['done']:
            print(f'Download done at {clock()}')
            break

        # 2) Download failed by local error
        elif share['error']:
            if ntry == maxtry:
                print(f'Stop downloading. Max tryout reached at {clock()}')
                break
            print(f'Retry downloading due to local error at {clock()}')
            ntry += 1
            time.sleep(1)
            continue

        # 3) Download failed by server issue
        elif not share['success']:
            print(f'Take a 10 minutes break due to server issue at {clock()}')
            time.sleep(10 * 60)
            continue

        # 4) Download success
        else:
            update_kwargs(kwargs, share['slice'])
            print(f"Time {clock()}, with \'slice\': {share['slice']}")
            time.sleep(1)

    # Script done
    if ntry == maxtry:
        print('Download Failure by some error.')
    print(f'Script Finished at {clock()}')
