from collections import defaultdict

from pandas import to_datetime

from kiwoom.config import types
from kiwoom.config.const import MARKETS, MARKET_GUBUNS
from kiwoom.config.types import STOCK, SECTOR
from kiwoom.data.preps import number, string, remove_sign
from kiwoom.utils import list_wrapper


"""
Global Variables (Int, Dictionary type)
  - Each variable's contents may change from time to time
  - For type dict, update it periodically by following ways 
    1) config.global_variable[key] = val
    2) config.global_variable.update({key1: val1, ..., keyn: valn})
    3) del config.global_variable[key] 
"""
# Download configuration
SPEEDING = False
DISCIPLINED = False
REQUEST_LIMIT_TIME = 3600
REQUEST_LIMIT_TRY = float('inf')
REQUEST_LIMIT_ITEM = float('inf')


# Download progress bar divisor
DOWNLOAD_PROGRESS_DISPLAY = 10


# Code lengths for each type
SECTOR_CODE_LEN = 3
STOCK_CODE_LENS = [6, 8, 9]  # 일반주식 = 6, 하이일드펀드 = 8, 신주인수권 = 9


# Periods
PERIODS = ['tick', 'min', 'day', 'week', 'month', 'year']


# 체결시간 예외 케이스 변환기 (in Regular Expression)
EXCEPTIONAL_DATETIME_REPLACER = {
    '888888$': '160000',  # 장마감 시간에 이루어진 거래 (16:00:00)
    '999999$': '180000'  # 시간외 종료에 이루어진 거래 (18:00:00)
}


# 예외적인 코드의 예외적인 체결시간 케이스 변환기
EXCEPTIONAL_DATETIME_REPLACER_FOR_EXCEPTIONAL_CODE = {
    '253': {  # K200 F 매수 콜매도
        '888888$': '170000',
        '999999$': '180000',
    },
    '254': {  # K200 F 매도 풋매도
        '888888$': '170000',
        '999999$': '180000',
    }
}


# 장 종료시간이 변경된 예외
EXCEPTIONAL_DATES = {
    # 'YYYYMMDD': delay(hour)
    '20201203': 1,  # 수능일 1시간 지연
    '20211118': 1,  # 수능일 1시간 지연
    '20221117': 1,  # 수능일 1시간 지연
    '20231116': 1  # 수능일 1시간 지연
}


"""
Configuration for downloading historical data.
  - methods : 'is_~' and 'get_~' as helper methods
  - global variables : market, market_gubun, sector and etc.
  - private variables : used by 'is_~' and 'get_~' methods
"""


def is_date(date):
    date = str(date)
    if len(date) != len('YYYYMMDD'):
        print(f"'date' must be in form 'YYYYMMDD', not {date}.")
        return False
    try:
        datetime = to_datetime(date, format=_PERIOD_TO_DATETIME_FORMAT['day'])
    except Exception:  # TypeError, ValueError
        print(f"'date' must be in form 'YYYYMMDD' with appropriate value, not {date}.")
        return False
    return True


def is_market(code):
    code = str(code)
    if code not in MARKETS:
        # print(f'Market code must be one of {MARKETS}')
        return False
    return True


def is_market_gubun(code):
    code = str(code)
    if code not in MARKET_GUBUNS:
        # raise ValueError(f'Market Gubun code must be one of {MARKET_GUBUNS}')
        return False
    return True


def is_sector(code):
    code = str(code)
    if len(code) == 3:
        return True
    return False


def get_code_type(code):
    """
    Returns whether code belongs to stock or sector.
    """
    if len(code) == SECTOR_CODE_LEN:
        return SECTOR
    # elif len(code) in STOCK_CODE_LENS:
    #    return STOCK
    else:
        # raise ValueError(f'Given code {code} is not a stock code nor a sector code.')
        return STOCK


def get_tr_code(periods, ctypes=None):
    """
    Returns TR code for given code type and period.

    :param ctypes: 'stock', 'sector', or list of ctype
    :param periods: 'tick', 'min', 'day', 'week', 'month', 'year', or list of period
    """
    tr_codes = list()
    periods = list_wrapper(periods)
    ctypes = list_wrapper(ctypes)

    for period in periods:
        if ctypes is None:
            tr_codes.extend([_PERIOD_TO_TR_CODE[period][ctype] for ctype in types.CodeType])
            continue
        tr_codes.extend([_PERIOD_TO_TR_CODE[period][ctype] for ctype in ctypes])

    if len(tr_codes) == 1:
        return tr_codes[0]
    return tr_codes


def get_period(tr_code):
    """
    Returns period for given TR code.
    Period can be one of  'tick', 'min', 'day', 'week', 'month' or 'year'.
    """
    return _TR_CODE_TO_PERIOD[tr_code]


def get_record_name_for_its_name(tr_code):
    return _CODE_TYPE_TO_RECORD_NAME[_TR_CODE_TO_CODE_TYPE[tr_code]]


def get_datetime_column(period):
    return _PERIOD_TO_DATETIME_COLUMN[period]


def get_datetime_format(period):
    return _PERIOD_TO_DATETIME_FORMAT[period]


def boost():
    global SPEEDING, DISCIPLINED
    SPEEDING = True
    DISCIPLINED = False

    global REQUEST_LIMIT_TIME, REQUEST_LIMIT_TRY, REQUEST_LIMIT_ITEM
    REQUEST_LIMIT_TIME = 550
    REQUEST_LIMIT_TRY = 1000
    REQUEST_LIMIT_ITEM = 99


def regret():
    global SPEEDING, DISCIPLINED
    SPEEDING = False
    DISCIPLINED = True

    global REQUEST_LIMIT_TIME, REQUEST_LIMIT_TRY, REQUEST_LIMIT_ITEM
    REQUEST_LIMIT_TIME = 3600
    REQUEST_LIMIT_TRY = float('inf')
    REQUEST_LIMIT_ITEM = float('inf')


def preper(tr_code, otype):
    """
    Returns needed keys to fetch and pre-processor for each key as a tuple

    :param tr_code: str
        one of TR codes listed in KOA Studio or API Manual Guide
    :param otype: OutputType
        type can be either single or multi
    :return: tuple
        each element in tuple has key and pre-processor for its key, i.e. ((key1, function1), ...)
    """
    return ((key, _PREP_FOR_OUTPUTS[key]) for key in _OUTPUTS_FOR_TR_CODE[tr_code][otype])


def inputs(tr_code, code, unit=None, end=None):
    """
    Returns an iterator of key, val for each TR request

    :param tr_code: str
    :param code: str
    :param unit: int/str
    :param end: str
    :param prev_next: str
    :return: iterator
    """
    # Copy needed inputs to modify
    inputs = dict(_INPUTS_FOR_TR_CODE[tr_code])

    # To set code with appropriate record name for each TR code
    record_name = get_record_name_for_its_name(tr_code)  # '종목코드' or '업종코드'
    inputs[record_name] = code

    # To set key, val for each different period
    use_unit = get_tr_code(['tick', 'min'])
    use_date = get_tr_code(['day', 'week', 'month', 'year'])

    if tr_code in use_unit:
        inputs['틱범위'] = str(unit) if unit else '1'
    elif tr_code in use_date:
        inputs['기준일자'] = str(end) if end else ''  # cf. 기준일자 != start
    else:
        raise KeyError(f'Tr_code must be one of opt10079 ~ opt10083.')
    return inputs.items()


def outputs(tr_code, otype):
    """
    Returns needed keys to fetch data for each OutputType

    :param tr_code: str
        one of TR codes listed in KOA Studio or API Manual Guide
    :param otype: OutputType
        type can be either SINGLE or MULTI
    :return: list
    """
    return _OUTPUTS_FOR_TR_CODE[tr_code][otype]


"""
Protected Variables
  - Instead of directly accessing to these variables, use get methods in this module 
"""
# Map period, code type to matching TR code
_PERIOD_TO_TR_CODE = {
    'tick': {
        STOCK: 'opt10079',
        SECTOR: 'opt20004'
    },
    'min': {
        STOCK: 'opt10080',
        SECTOR: 'opt20005'
    },
    'day': {
        STOCK: 'opt10081',
        SECTOR: 'opt20006'
    },
    'week': {
        STOCK: 'opt10082',
        SECTOR: 'opt20007'
    },
    'month': {
        STOCK: 'opt10083',
        SECTOR: 'opt20008'
    },
    'year': {
        STOCK: 'opt10094',
        SECTOR: 'opt20019'
    }
}

# Map TR code to matching period
_TR_CODE_TO_PERIOD = {
    tr_code: period for period, tr_dic in _PERIOD_TO_TR_CODE.items() for ctype, tr_code in tr_dic.items()
}

# Map TR code to code type
_TR_CODE_TO_CODE_TYPE = {
    tr_code: ctype for tr_dic in _PERIOD_TO_TR_CODE.values() for ctype, tr_code in tr_dic.items()
}

# Map code type to record name to fetch code from downloaded data
_CODE_TYPE_TO_RECORD_NAME = {
    STOCK: '종목코드',
    SECTOR: '업종코드'
}

# Datetime column name for each period
_PERIOD_TO_DATETIME_COLUMN = {
    'tick': '체결시간',
    'min': '체결시간',
    'day': '일자',
    'week': '일자',
    'month': '일자',
    'year': '일자'
}

# Pandas parsing format of datetime column for each period
_PERIOD_TO_DATETIME_FORMAT = {
    # YYYYMMDDHHMMSS = %Y%m%d%H%M%S
    'tick': '%Y%m%d%H%M%S',
    'min': '%Y%m%d%H%M%S',
    'day': '%Y%m%d',
    'week': '%Y%m%d',
    'month': '%Y%m%d',
    'year': '%Y%m%d'
}


"""
Configuration for pre-process
"""
# How to pre-process for each output
__PREP_FOR_OUTPUTS = {
    number: [
        '평가손익', '총평가손익금액', '수익률(%)',
        '총수익률(%)', '주문가격', '주문번호',
        '주문수량', '예수금',  '보유수량',
        '매입가', '전일종가', '미체결수량',
        '체결량', '거래량', '거래대금'
    ],
    string: [
        '종목번호', '종목코드', '업종코드',
        '종목명', '주문상태', '일자',
        '체결시간', '주문구분'
    ],
    remove_sign: [
        '현재가', '시가', '고가', '저가'
    ]
}

# Revert dictionary to be in the form of {'key': function}
_PREP_FOR_OUTPUTS = defaultdict(
    lambda: string,
    {val: key for key, vals in __PREP_FOR_OUTPUTS.items() for val in vals}
)


"""
Configuration for inputs and outputs
"""
# Inputs needed for each TR code request
_INPUTS_FOR_TR_CODE = {
    'opt10079': {  # 주식틱차트조회요청
        '종목코드': None,
        '틱범위': None,
        '수정주가구분': '1'
    },
    'opt10080': {  # 주식분봉차트조회요청
        '종목코드': None,
        '틱범위': None,
        '수정주가구분': '1'
    },
    'opt10081': {  # 주식일봉차트조회요청
        '종목코드': None,
        '기준일자': None,
        '수정주가구분': '1'
    },
    'opt10082': {  # 주식주봉차트조회요청
        '종목코드': None,
        '기준일자': None,
        '끝일자': None,
        '수정주가구분': '1'
    },
    'opt10083': {  # 주식월봉차트조회요청
        '종목코드': None,
        '기준일자': None,
        '끝일자': None,
        '수정주가구분': '1'
    },
    'opt10094': {  # 주식년봉차트조회요청
        '종목코드': None,
        '기준일자': None,
        '끝일자': None,
        '수정주가구분': '1'
    },
    'opt20001': {  # 업종현재가요청
        '시장구분': None,
        '업종코드': None
    },
    'opt20002': {  # 업종별주가요청
        '시장구분': None,
        '업종코드': None
    },
    'opt20003': {  # 전업종지수요청
        '업종코드': None
    },
    'opt20004': {  # 업종틱차트조회요청
        '업종코드': None,
        '틱범위': None
    },
    'opt20005': {  # 업종분봉조회요청
        '업종코드': None,
        '틱범위': None
    },
    'opt20006': {  # 업종일봉조회요청
        '업종코드': None,
        '기준일자': None
    },
    'opt20007': {  # 업종주봉조회요청
        '업종코드': None,
        '기준일자': None
    },
    'opt20008': {  # 업종월봉조회요청
        '업종코드': None,
        '기준일자': None
    },
    'opt20009': {  # 업종현재가일별요청
        '시장구분': None,
        '업종코드': None
    },
    'opt20019': {  # 업종년봉조회요청
        '업종코드': None,
        '기준일자': None
    },
}

# Outputs for each TR code in the form of {'TR code': [[single data], [multi data]]}
_OUTPUTS_FOR_TR_CODE = {
    'opt10079': [  # 주식틱차트조회요청
        ['종목코드', '마지막틱갯수'],
        [
            '체결시간', '현재가', '거래량'
        ]
    ],
    'opt10080': [  # 주식분봉차트조회요청
        ['종목코드'],
        [
            '체결시간', '시가', '고가',
            '저가', '현재가', '거래량'
        ]
    ],
    'opt10081': [  # 주식일봉차트조회요청
        ['종목코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt10082': [  # 주식주봉차트조회요청
        ['종목코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt10083': [  # 주식월봉차트조회요청
        ['종목코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt10094': [  # 주식년봉차트조회요청
        ['종목코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt20004': [  # 업종틱차트조회요청
        ['업종코드'],
        [
            '체결시간', '현재가', '거래량'
        ]
    ],
    'opt20005': [  # 업종분봉조회요청
        ['업종코드'],
        [
            '체결시간', '시가', '고가',
            '저가', '현재가', '거래량'
        ]
    ],
    'opt20006': [  # 업종일봉조회요청
        ['업종코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt20007': [  # 업종주봉조회요청
        ['업종코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt20008': [  # 업종월봉조회요청
        ['업종코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
    'opt20019': [  # 업종년봉조회요청
        ['업종코드'],
        [
            '일자', '시가', '고가',
            '저가', '현재가', '거래량',
            '거래대금'
        ]
    ],
}
