from os import getcwd, makedirs
from os.path import exists, join
from textwrap import dedent
from traceback import format_exc
from warnings import warn

import pandas as pd

from kiwoom import config
from kiwoom.config import history
from kiwoom.config.error import msg
from kiwoom.config.types import MULTI
from kiwoom.core.kiwoom import Kiwoom
from kiwoom.data.preps import string
from kiwoom.utils.general import date, name
from kiwoom.utils.manager import Downloader


class Server:
    def __init__(self):
        self.api: Kiwoom = None
        self.share = None

    def init(self, api, share):
        self.api = api
        self.share = share

    """
    Default slots to the most basic two events.
        on_event_connect
        on_receive_msg
    """
    # Default event slot for on_event_connect
    def login(self, err_code):
        """
        Default slot for 'on_event_connect'

        When Kiwoom.on_event_connect(...) is called, this method will be automatically called.
        """
        print(f'\n로그인 {msg(err_code)}')
        print(f'\n* 시스템 점검\n  - 월 ~ 토 : 05:05 ~ 05:10\n  - 일 : 04:00 ~ 04:30\n')
        self.api.unloop()

    # Default event slot for on_receive_msg_slot
    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        """
        Default slot for 'on_receive_msg'

        Whenever the server sends a message, this method prints depending on below.
        >> Kiwoom.message(True)
        >> Kiwoom.message(False)
        """
        if self.api.msg:
            print(f'\n화면번호: {scr_no}, 요청이름: {rq_name}, TR코드: {tr_code} \n{msg}\n')

    """
    Basic methods
    """
    @Downloader.handler
    def history(self, scr_no, rq_name, tr_code, _, prev_next):
        kwargs = self.share.get_args(name())
        period = history.get_period(tr_code)

        rec = history.get_record_name_for_its_name(tr_code)  # record_name = '종목코드' | '업종코드'
        code = string(self.api.get_comm_data(tr_code, rq_name, 0, rec))

        # Handle trading suspended stock
        if not code:  # code = ''
            code = kwargs['code']

        # Check if wrong data received
        if code != kwargs['code']:
            raise RuntimeError(f"Requested {kwargs['code']}, but the server still sends {code}.")

        # Fetch multi data
        data = {key: list() for key in history.outputs(tr_code, MULTI)}
        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
        for i in range(cnt):
            for key, fn in history.preper(tr_code, MULTI):
                data[key].append(fn(self.api.get_comm_data(tr_code, rq_name, i, key)))

        # Update downloaded data
        for key in data.keys():
            self.share.extend_history(code, key, data[key])

        # If data is more than needed, then stop downloading.
        if 'start' in kwargs:
            col = history.get_datetime_column(period)
            # To check whether it's an empty data.
            if len(data[col]) > 0:
                last = data[col][-1][:len('YYYYMMDD')]
                # Note that data is ordered from newest to oldest
                if date(last) < date(kwargs['start']):
                    prev_next = ''

        # Continue to download
        if prev_next == '2':
            try:
                # Call signal method again, but with prev_next='2'
                bot = self.api.signal('on_receive_tr_data', name())
                bot(code, period=period, prev_next=prev_next)
            except Exception as err:
                args = f"code={code}, period={period}, prev_next={prev_next}"
                self.share.update_single('history', 'error', True)
                print(f"An error at Bot.history({args}).\n\n{format_exc()}")

        # Download done
        else:
            # Sort to chronological order
            df = pd.DataFrame(self.share.get_history(code))[::-1]

            # To make df have datetime index
            col = history.get_datetime_column(period)
            fmt = history.get_datetime_format(period)

            """
                Make time-related column as pandas Datetime index
            """
            # To handle exceptional time and dates
            if not df.empty and history.is_sector(code) and col == '체결시간':
                # To choose exceptional datetime replacer
                edrfec = history.EXCEPTIONAL_DATETIME_REPLACER_FOR_EXCEPTIONAL_CODE
                replacer = edrfec[code] if code in edrfec else history.EXCEPTIONAL_DATETIME_REPLACER

                # Find index of dates that delayed market opening time and inconvertibles in df
                indices = dict()
                exceptions = list()
                start, end = date(df[col].iat[0][:len('YYYYMMDD')]), date(df[col].iat[-1][:len('YYYYMMDD')])
                for ymd, delay in history.EXCEPTIONAL_DATES.items():
                    if start <= date(ymd) <= end:
                        day = df[col].loc[df[col].str.match(ymd)]
                        indices[ymd] = day.index

                        # To save original data
                        for regex, datetime in replacer.items():
                            series = day.loc[day.str.contains(regex, regex=True)]
                            series = series.replace(regex={regex: datetime})
                            series = pd.to_datetime(series, format='%Y%m%d%H%M%S')
                            exceptions.append(series)

                # Replace inconvertibles (888888, 999999) to (16:00:00, 18:00:00)
                df[col].replace(regex=replacer, inplace=True)

                # To make column as pandas datetime series
                df[col] = pd.to_datetime(df[col], format=fmt)

                # Subtract delayed market time as if it pretends to start normally
                for ymd, idx in indices.items():
                    delay = history.EXCEPTIONAL_DATES[ymd]
                    df.loc[idx, col] -= pd.DateOffset(hours=delay)

                # Replace subtracted exceptional times back to original
                for series in exceptions:
                    df.loc[series.index, col] = series

            # col='일자' or including df.empty for both col
            else:
                df[col] = pd.to_datetime(df[col], format=fmt)

            # Finally make datetime column as index
            df.set_index(col, inplace=True)

            """
                Close downloading process
            """
            # To get rid of data preceding 'start'
            if 'start' in kwargs:
                df = df.loc[kwargs['start']:]
            # To get rid of data following 'end'
            if 'end' in kwargs:
                df = df.loc[:kwargs['end']]

            # If server sent mixed data
            if not df.index.is_monotonic_increasing:
                raise RuntimeError(
                    f'Downloaded data is not monotonic increasing. Error at Server.history() with code={code}.'
                )

            # Rename column
            if period == 'tick':
                df.rename(columns={'현재가': '체결가'}, inplace=True)

            # Save data to csv file
            self.history_to_csv(df, code, kwargs['path'], kwargs['merge'], kwargs['warning'])

            # Once common variables are used, delete it
            self.share.remove_args(name())
            self.share.remove_history(code)

            # Mark successfully downloaded
            self.share.update_single(name(), 'complete', True)

            self.api.disconnect_real_data(scr_no)
            self.api.unloop()

    def history_to_csv(self, df, file, path=None, merge=False, warning=True):
        """
        Save historical data of given code at path in .csv format.

        Once the data is saved, it will be removed from the memory.
        When merge is True, data will be merged with existing file.
        Data will be overwritten by default, otherwise.

        :param df: pandas.Dataframe
        :param file: str
        :param path: str
        :param merge : bool
        :param warning: bool
        """
        # In case, path is '' or None
        if not path:
            path = getcwd()

        if not exists(path):
            makedirs(path)

        file = file if file.endswith('.csv') else file + '.csv'
        file = join(path, file)

        if merge:
            # No file to merge with
            if not exists(file):
                # An empty file will be created later
                pass

            # Nothing to be done
            elif df.empty:
                return

            # To merge with existing data
            else:
                col = df.index.name
                if col not in ['일자', '체결시간']:
                    raise ValueError(f"No column matches '일자' or '체결시간'. Merge can't be done.")

                # Existing data
                if 'file' in self.share.single['history']:
                    db = self.share.get_single('history', 'file')
                else:
                    # Read the existing file from disk
                    db = pd.read_csv(
                        file,
                        index_col=[col],
                        parse_dates=[col],
                        encoding=config.ENCODING
                    )
                db.dropna(axis='index', inplace=True)

                if not db.empty:
                    # To check db has more past data, at least the same
                    assert (db.index[0] <= df.index[0]), \
                        f"Existing file starts from {db.index[0]}, while given data from {df.index[0]}."

                    # To check db is chronologically ordered
                    assert db.index.is_monotonic_increasing, \
                        f"The existing file, {file}, is not sorted in chronological order."

                    try:
                        start = db.index.get_loc(df.index[0])
                        # To handle multiple same timestamps
                        if isinstance(start, slice):
                            start = start.start

                        db = db.iloc[:start]
                        df = pd.concat([db, df], axis=0, join='outer', copy=False)

                    except KeyError:
                        err_msg = dedent(
                            f"""
                            Data, '{file}', is forced to be merged but it may not be time-continuous.
                             - The End of the Existing Data : {db.index[-1]}
                             - The Start of Downloaded Data : {df.index[0]}
                            """
                        )
                        # Note that tick data may change depending on downloading time
                        # Kiwoom server may calibrate data after market close (in my opinion)
                        if col == '체결시간':  # tick, min
                            start_date = df.index[0].date()
                            if warning:
                                # The case data may not be time-continuous
                                if db.loc[db.index == start_date].empty:
                                    warn(err_msg)
                            # To slice DB before the date when downloaded data starts from
                            db = db[:start_date]

                        # The case data may not be time-continuous
                        else:  # col == '일자'  # day, week, month, year
                            if warning:
                                warn(err_msg)

                        # Just concatenate if no overlapping period.
                        df = pd.concat([db, df], axis=0, join='outer', copy=False)

        if not df.index.is_monotonic_increasing:
            raise RuntimeError(
                f'Error at Server.history_to_csv(file={file}, ...)/\n'
                + 'File to write is not monotonic increasing with respect to time.'
            )

        # To prevent overwriting
        if not merge and exists(file):
            raise FileExistsError(
                f'Error at Server.history_to_csv(file={file}, ...)/\n'
                + "File already exists. Set merge=True or move the file to prevent from losing data."
            )

        # Finally write to csv file
        df.to_csv(file, encoding=config.ENCODING)
