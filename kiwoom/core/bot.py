from kiwoom import config
from kiwoom.config import history
from kiwoom.config.history import ExitCode
from kiwoom.config.screen import Screen
from kiwoom.core.kiwoom import Kiwoom
from kiwoom.core.server import Server
from kiwoom.data.share import Share
from kiwoom.utils.general import *
from kiwoom.utils.manager import timer, Downloader

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from time import time
from os import getcwd
from os.path import join
from textwrap import dedent
from traceback import format_exc
from pandas import read_csv, DateOffset, Timestamp


class Bot:
    def __init__(self, server=None):
        self.api = Kiwoom()
        self.scr = Screen()
        self.share = Share()

        # Connect server as a slot
        self.server = server if issubclass(type(server), Server) else Server()
        self.default_connect(server)
        self.server.init(api=self.api, share=self.share)

    def default_connect(self, server):
        self.api.set_connect_hook('on_receive_tr_data', 'rq_name')
        self.api.connect('on_receive_tr_data', signal=self.history, slot=self.server.history)
        self.api.connect('on_event_connect', signal=self.login, slot=self.server.login)
        self.api.connect('on_receive_msg', slot=self.server.on_receive_msg)

    @timer
    def login(self):
        self.api.comm_connect()
        self.api.loop()

    def connected(self):
        """
        Returns whether Bot is currently connected to server

        :return: bool
        """
        state = self.api.get_connect_state()
        if state == 1:
            return True
        return False

    def stock_list(self, market):
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
        QTest.qWait(history.request_limit_time)

        ctype = history.get_code_type(code)  # ctype = 'stock' | 'sector'
        tr_code = history.get_tr_code(period, ctype)

        """
            Setting args just for once.
        """
        if prev_next == '0':
            # In case path is '' or None
            if not path:
                path = getcwd()

            # To share variables with Slot
            kwargs = effective_args(locals(), remove=['ctype', 'tr_code'])
            self.share.update_single(name(), 'error', False)
            self.share.update_single(name(), 'restart', False)
            self.share.update_single(name(), 'complete', False)
            self.share.update_single(name(), 'impossible', False)

            # To check format of input dates
            if 'start' in kwargs:
                if not history.is_date(start):
                    raise ValueError(f"Given 'start' {start} is not a valid date.")
            if 'end' in kwargs:
                if not history.is_date(end):
                    raise ValueError(f"Given 'end' {end} is not a valid date.")

            """
                Check 'start' and 'end' points to save downloading time. 
            """
            if merge:
                try:
                    file = join(path, code + '.csv')
                    col = history.get_datetime_column(period)
                    df = read_csv(
                        file,
                        index_col=[col],
                        parse_dates=[col],
                        encoding=config.encoding
                    )

                    if period in ['tick', 'min']:
                        # Last tick for stock is 15:30 and for sector is 18:00
                        h, m = (15, 30) if ctype is history.stock else (18, 00)  # else for sector
                        last_day = date(df.index[-1])
                        last_tick_of_day = Timestamp(df.index[-1]).replace(hour=h, minute=m)
                        download_completed = last_tick_of_day <= df.index[-1]

                        # To push 'start' date further as much as possible. If None, set newly.
                        if 'start' not in kwargs or date(kwargs['start']) <= last_day:
                            if download_completed:
                                # Start from the day after last day
                                kwargs['start'] = str((last_day + DateOffset(1)).date()).replace('-', '')
                            else:
                                # Start from the last day
                                kwargs['start'] = str(last_day).replace('-', '')

                        # If downloading is not needed, just return
                        if 'end' in kwargs:
                            if download_completed:
                                if date(kwargs['end']) <= last_day:
                                    self.share.update_single(name(), 'complete', True)
                                    return

                    else:  # if period in ['day', 'week', 'year']
                        last_day = date(df.index[-1])
                        # To push 'start' date further as much as possible. If None, set newly.
                        if 'start' not in kwargs or date(kwargs['start']) <= last_day:
                            # Start from the last day
                            kwargs['start'] = str(last_day).replace('-', '')

                        # If downloading is not needed, just return
                        if 'end' in kwargs:
                            if date(kwargs['end']) < last_day:
                                self.share.update_single(name(), 'complete', True)
                                return

                    # Resolve memory issues
                    del df

                # If any exception, just skip
                except Exception as err:
                    pass

            """
                Update and print arguments. 
            """
            # Done arg setting
            self.share.update_args(name(), kwargs)

            # Print args
            f = lambda key: f"'{kwargs[key]}'" if key in kwargs else None
            print(f"{{code={f('code')}, start={f('start')}, end={f('end')}, period={f('period')}}}")

        """
            Start downloading.
        """
        # Check requesting status
        self.share.single['histories']['nrq'] += 1
        if history.speeding:
            if self.share.get_single('histories', 'nrq') >= history.request_limit_try:
                # Set back to default configuration
                if self.share.get_single('histories', 'cnt') == 0:
                    self.share.update_single('history', 'impossible', True)
                self.share.update_single(name(), 'restart', True)
                self.api.unloop()
                return

        # Finally request data to server
        for key, val in history.inputs(tr_code, code, unit, end):
            self.api.set_input_value(key, val)
        scr_no = self.scr.alloc(tr_code, code)

        # If comm_rq_data returns non-zero error code, restart downloading
        if self.api.comm_rq_data(name(), tr_code, prev_next, scr_no) != 0:
            self.share.update_single('history', 'restart', True)
            self.api.unloop()
            return

        # Wait response from the server
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
            if download restart is needed, returns slice that can be used in the next run
        """
        if not path:
            path = getcwd()

        # Initialize status
        self.share.update_single(name(), 'nrq', 0)  # number of request
        self.share.update_single(name(), 'cnt', 0)  # number of stocks
        self.share.update_args(name(), effective_args(locals()))

        """
            Validate given arguments
        """
        # To decide what to download
        lst, ctype, mname = None, None, None
        if not any([market, sector]) or all([market, sector]):
            raise RuntimeError("Download target must be either of 'market' or 'sector'.")
        elif market is not None:
            lst, ctype, mname = self.stock_list(market), history.stock, history.markets[market]
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

        """
            Start downloading
        """
        # To Download
        status = ''
        begin = time()
        print(f'Download Start for {len(lst)} {ctype}s in {mname}.')
        print(f' - Encoding : {config.encoding}\n - DataPath : {path}')

        for i, code in enumerate(lst):
            if i % divisor == 0:
                pct = (i / len(lst)) * 100
                print(f'\nDownloading ..\t{pct: .1f}% ({i} of {len(lst)})')

            # Try downloading
            try:
                self.history(code, period, unit=unit, start=start, end=end, path=path, merge=merge, warning=warning)

            # 1) Error with starting Bot.history() (at the first call)
            except Exception:
                args = unpack_args(self.share.get_args('history'))
                print(f"\nAn error at Bot.history({args}).\n\n{format_exc()}")
                return ExitCode.failure

            # 2) Error with continuing Bot history() (at least second call, by prev_next='2')
            if self.share.get_single('history', 'error'):
                # Note that error message will be printed by Server.history()
                return ExitCode.failure

            # 3) Error with reaching the request limit or error with server freezing
            elif self.share.get_single('history', 'restart'):
                # If it's impossible to download with the trick
                if self.share.get_single('history', 'impossible'):
                    print(f"\n[{clock()}] The {ctype} {code} can't be downloaded with speeding.")
                    return ExitCode.impossible
                break

            # 4) Error that Server.history() couldn't be finished.
            elif not self.share.get_single('history', 'complete'):
                # Give one more last chance
                print(f'\n[{clock()}] Try to restart downloading for {code}.\n')
                self.history(code, period, unit=unit, start=start, end=end, path=path, merge=merge, warning=warning)

                # If it fails again, stop downloading.
                if not self.share.get_single('history', 'complete'):
                    slice = (from_ + self.share.single[name()]['cnt'], to_)
                    print(f"\n[{clock()}] Run Bot.histories() with slice={slice} or code='{code}' for the next time.")
                    return ExitCode.failure

            """
                Download completed for one item in the list
            """
            # Finally successfully downloaded
            self.share.single[name()]['cnt'] += 1

            # 5) Successfully downloaded with disciplined, but it's time for speeding again.
            if history.disciplined:
                status = f"[{clock()}] The program needs to be restarted for speeding again."
                break

            # 6) Successfully downloaded but exceeds request limit items
            if history.speeding:
                # Restarts the program
                if self.share.single[name()]['cnt'] >= history.request_limit_item:
                    break

        """
            Close downloading
        """
        cnt = self.share.get_single(name(), 'cnt')
        msg = dedent(
            f"""
            Download Done for {100 * cnt / len(lst) if lst else 100: .1f}% ({cnt} of {len(lst)}) {ctype}s in {mname}.
            Download Time : {(time() - begin) / 60: .1f} minutes (with {self.share.single[name()]['nrq']} requests)\n
            """
        ) + status
        print(msg)

        # If complete
        if cnt == len(lst):
            return ExitCode.success
        # Else return remaining items
        return from_ + cnt, to_

    def exit(self, rcode=0):
        """
        Close all windows open and exit the application that runs this bot

        :param rcode: int
            return code when exiting the program
        """
        app = QApplication.instance()
        app.closeAllWindows()
        app.exit(rcode)
