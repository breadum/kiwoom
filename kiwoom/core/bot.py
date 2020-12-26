from kiwoom import Kiwoom
from kiwoom import config
from kiwoom.config import history
from kiwoom.config.error import ExitCode
from kiwoom.config.screen import Screen
from kiwoom.data.share import Share
from kiwoom.utils import clock, effective_args, name
from kiwoom.utils.manager import timer, Downloader

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from time import time
from os import getcwd
from os.path import join, getsize
from pandas import read_csv, DateOffset, Timestamp


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

class Bot:
    def __init__(self, slot=None):
        self.api = Kiwoom()
        self.scr = Screen()
        self.share = Share()

        # Connect
        if slot is not None:
            if issubclass(type(slot), slot):
                self.server = slot



    def init(self, **kwargs):
        """
        Set attributes by key = val in kwargs

        Dynamically assign attributes for this class as self.key = val
        :param kwargs: str=any
            key=val, key1=val1, ...
        """
        for key, val in kwargs.items():
            setattr(self, key, val)

    @timer
    def login(self):
        self.api.comm_connect()
        self.api.loop()

    def connected(self):
        state = self.api.get_connect_state()
        if state == 1:
            return True
        return False

    def code_list(self, market):
        """
        Returns all stock codes in the given market

        :param market: str
            one of market code in kiwoom.config.markets
        """
        market = str(market)
        if history.is_market(market):
            return sorted(self.api.get_code_list_by_market(market).split(';')[:-1])

    def sector_list(self, market_gubun):
        """
        Returns all sector codes in the given market_gubun

        :param market_gubun: str
            one of market_gubun code in kiwoom.config.market_gubuns
        """
        market_gubun = str(market_gubun)
        if history.is_market_gubun(market_gubun):
            lst = list()
            sectors = self.api.koa_functions('GetUpjongCode', market_gubun)
            for sector in sectors.split('|')[:-1]:
                lst.append(sector.split(',')[1])
            return sorted(lst)

    def history(
            self,
            code,
            period,
            unit=None,
            start=None,
            end=None,
            path=None,
            merge=True,
            warning=True,
            prev_next='0'
    ):
        """
        Download historical market data of given code and save it as csv to given path

        :param code: str
            unique code of stock or sector
        :param period: str
            one of tick, min, day, week, month and year
        :param unit: int
            1, 3, 5, 10, 30 etc.. (cf. 1 bar = unit * period)
        :param start: str
            string of start day in format 'YYYYMMDD'
        :param end: str
            string of end day in format 'YYYYMMDD'. if None, until now by default.
        :param path: str
            path to save downloaded data
        :param merge: bool
            whether to merge data with existing file or to overwrite it
        :param warning: bool
            turn on/off the warning message if any
        :param prev_next: str
            this param is given by the response from the server. default is '0'
        """
        # Wait for default request limit, 3600 ms
        QTest.qWait(config.request_limit_time)

        ctype = history.get_code_type(code)  # ctype = 'stock' | 'sector'
        tr_code = history.get_tr_code(period, ctype)

        # If download starts, set args for only once.
        if prev_next == '0':
            # In case path is '' or None
            if not path:
                path = getcwd()

            # To share variables with Slot
            kwargs = effective_args(locals(), remove=['ctype', 'tr_code'])
            self.share.update_single(name(), 'reboot', False)
            self.share.update_single(name(), 'success', False)

            # To check format of input dates
            if 'start' in kwargs:
                if not history.is_date(start):
                    raise ValueError(f"Given 'start' {start} is not a valid date.")
            if 'end' in kwargs:
                if not history.is_date(end):
                    raise ValueError(f"Given 'end' {end} is not a valid date.")

            # To save time, find out lastly downloaded data and change 'start' point
            if merge and period in ['tick', 'min']:
                try:
                    file = join(path, code + '.csv')
                    if getsize(file) / (1024 * 1024) > 100:  # if size > 100MB
                        raise UserWarning(f'File {file} is too big to merge. Please split file.')

                    col = history.get_datetime_column(period)
                    df = read_csv(
                        file,
                        index_col=[col],
                        parse_dates=[col],
                        encoding=config.encoding
                    )

                    # Last tick for stock is 15:30 and for sector is 18:00
                    h, m = (15, 30) if ctype is history.stock else (18, 00)  # else for sector
                    last_day = Timestamp(df.index[-1]).date()
                    last_tick_of_day = Timestamp(df.index[-1]).replace(hour=h, minute=m)
                    download_completed = last_tick_of_day <= df.index[-1]

                    # Resolve memory issues
                    del df

                    # To push 'start' date further as much as possible. If None, set newly.
                    if 'start' not in kwargs or Timestamp(kwargs['start']).date() <= last_day:
                        if download_completed:
                            # start from the day after last day
                            kwargs['start'] = str((last_day + DateOffset(1)).date()).replace('-', '')
                        else:
                            # start from the last day
                            kwargs['start'] = str(last_day).replace('-', '')

                    # If downloading is not needed, just return
                    if 'end' in kwargs:
                        if download_completed:
                            if Timestamp(kwargs['end']).date() <= last_day:
                                self.share.update_single(name(), 'success', True)
                                return

                # If any exception other than UserWarning, just skip
                except Exception as err:
                    # If file is too big, raise UserWarning
                    if type(err) == UserWarning:
                        raise UserWarning(err)
                    pass

            # Done arg setting
            self.share.update_args(name(), kwargs)

        # Check requesting status
        self.share.single['histories']['nrq'] += 1
        if self.share.get_single('histories', 'nrq') >= config.request_limit_try:
            self.share.update_single('history', 'reboot', True)
            self.api.unloop()
            return

        # Finally request data to server
        kwargs = {'unit': unit, 'end': end, 'prev_next': prev_next}
        for key, val in history.inputs(tr_code, code, **kwargs):
            self.api.set_input_value(key, val)
        scr_no = self.scr.alloc(tr_code, code)
        self.api.comm_rq_data(name(), tr_code, prev_next, scr_no)
        self.api.loop()

    @Downloader.watcher
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
        """
        Download historical data of partial or all items in given market/sector and save it as csv file.

        :param market: str
            one of market type in string
        :param sector: str
            one of market gubuns in string
        :param period: str
            one of tick, min, day, week, month and year
        :param unit: int
            1, 3, 5, 10, 30 etc.. (cf. 1 bar = unit * period)
        :param start: str
            string of start day in format 'YYYYMMDD'
        :param end: str
            string of end day in format 'YYYYMMDD'. if None, until now by default.
        :param path: str
            path to save downloaded data
        :param slice: tuple of int
            partially download from the whole items in specific market.
            slice can be one of (from, to), (from, None) or (None, to)
        :param code: str
            unique code of stock or sector to start downloading from.
        :param merge: bool
            whether to merge data with existing file or to overwrite it
        :param warning: bool
            turn on/off the warning message if any

        :return: int or tuple
            if successfully download all, returns 0 (= ExitCode.success)
            if download failed by local errors, returns -1 (= ExitCode.failure)
            if download stopped due to server reboot, returns slice that can be used in the next run
        """
        if not path:
            path = getcwd()

        # Save status
        self.share.update_single(name(), 'nrq', 0)  # number of request
        self.share.update_single(name(), 'cnt', 0)  # number of stocks
        self.share.update_args(name(), effective_args(locals()))

        # To decide what to download
        lst, ctype, mname = None, None, None
        if not any([market, sector]) or all([market, sector]):
            raise RuntimeError("Download target must be either of 'market' or 'sector'.")
        elif market is not None:
            lst, ctype, mname = self.code_list(market), history.stock, history.markets[market]
        elif sector is not None:
            lst, ctype, mname = self.sector_list(sector), history.sector, history.market_gubuns[sector]

        # Set the portion in download list
        from_, to_ = None, None
        if all([slice, code]):
            raise RuntimeError("Only one option is available: either of 'slice' or 'start_code'.")
        # Option1 - Slice
        elif slice is not None:
            try:
                from_, to_ = slice
            except ValueError:
                raise ValueError(f'Slice must be (from, to), (from, None), or (None, to) not {slice}.')
        # Option2 - Code
        elif code is not None:
            from_, to_ = lst.index(code), None
        # Fully download
        else:
            from_, to_ = 0, None

        # Select target in download list
        lst = lst[from_: to_]

        # To print progress bar
        divisor = history.download_progress_display
        if len(lst) < 4 * divisor:
            # At least print 25% of progress if possible
            divisor = max(1, len(lst) // 4)

        # To Download
        begin = time()
        print(f'Download Start for {len(lst)} {ctype}s in {mname}.')
        print(f' - Encoding : {config.encoding}\n - DataPath : {path}')

        for i, code in enumerate(lst):
            if i % divisor == 0:
                pct = (i / len(lst)) * 100
                print(f'Downloading ..\t{pct: .1f}% ({i} of {len(lst)})')

            # Try downloading
            try:
                self.history(code, period, unit=unit, start=start, end=end, path=path, merge=merge, warning=warning)
            except Exception as err:
                print(f'An error occurred at Signal.history(code={code}, ...).\n{err}')
                return ExitCode.failure

            # If reboot is needed, stop downloading
            if self.share.get_single('history', 'reboot'):
                print(f'Server does not response at {clock()}')
                break

            # If an error occurred, try again
            if not self.share.get_single('history', 'success'):
                print(f'Downloading restarts from {code}.\n')
                self.history(code, period, unit=unit, start=start, end=end, path=path, merge=merge, warning=warning)
                # If it fails again, stop downloading.
                if not self.share.get_single('history', 'success'):
                    print(f"Downloading stops. Restart with slice={(from_ + self.share.single[name()]['cnt'], to_)}")
                    return ExitCode.failure

            # To count successfully downloaded codes
            self.share.single[name()]['cnt'] += 1

        cnt = self.share.get_single(name(), 'cnt')
        print(f'Downloading ..\t{100 * cnt / len(lst): .1f}% ({cnt} of {len(lst)})')
        print(f'Download Done for {cnt} {ctype}s in {mname}.')
        print(f'Download Time : {(time() - begin) / 60: .1f} minutes\n')

        # If done, return success exit code
        if cnt == len(lst):
            return ExitCode.success
        # Else, return the remaining stocks as a slice
        print(f'Please re-start from slice={(from_ + cnt, to_)}')
        return (from_ + cnt, to_)

    def exit(self, rcode):
        """
        Close all windows open and exit the application that runs this bot

        :param rcode: int
            return code when exiting the program
        """
        app = QApplication.instance()
        app.closeAllWindows()
        app.exit(rcode)
