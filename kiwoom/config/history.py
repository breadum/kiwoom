from collections import defaultdict
from pandas import to_datetime
from kiwoom.config import types, markets, market_gubuns, sectors
from kiwoom.config.types import single, multi
from kiwoom.utils import list_wrapper
from kiwoom.data.prep import number, string, remove_sign


"""
Global Variables (Int, Dictionary type)
  - Each variable's contents may change from time to time
  - For type dict, update it periodically by following ways 
    1) config.global_variable[key] = val
    2) config.global_variable.update({key1: val1, ..., keyn: valn})
    3) del config.global_variable[key] 
"""
# Download progress bar divisor
download_progress_display = 10

# Code types
stock = types.CodeType.stock
sector = types.CodeType.sector

# Code lengths for each type
sector_code_len = 3
stock_code_lens = [6, 9]  # 일반주식 = 6, 신주인수권 = 9

# Periods
periods = ['tick', 'min', 'day', 'week', 'month', 'year']

# 체결시간 예외 케이스 변환기 (in Regular Expression)
exceptional_datetime_replacer = {
    '888888$': '160000',  # 장마감 시간에 이루어진 거래 (16:00:00)
    '999999$': '180000'  # 시간외 종료에 이루어진 거래 (18:00:00)
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
        datetime = to_datetime(date, format=_period_to_datetime_format['day'])
    except Exception:  # TypeError, ValueError
        print(f"'date' must be in form 'YYYYMMDD' with appropriate value, not {date}.")
        return False
    return True


def is_market(code):
    code = str(code)
    if code not in markets:
        print(f'Market code must be one of {markets}')
        return False
    return True


def is_market_gubun(code):
    code = str(code)
    if code not in market_gubuns:
        raise ValueError(f'Market Gubun code must be one of {market_gubuns}')
    return True


def is_sector(code):
    code = str(code)
    if code not in sectors:
        raise ValueError(f'Sector code must be one of {sector}')
    return True


def get_code_type(code):
    """
    Returns whether code belongs to stock or sector.
    """
    if len(code) == sector_code_len:
        return sector
    elif len(code) in stock_code_lens:
        return stock
    else:
        raise ValueError(f'Given code {code} is not a stock code nor a sector code.')


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
            tr_codes.extend([_period_to_tr_code[period][ctype] for ctype in types.CodeType])
            continue
        tr_codes.extend([_period_to_tr_code[period][ctype] for ctype in ctypes])

    if len(tr_codes) == 1:
        return tr_codes[0]
    return tr_codes


def get_period(tr_code):
    """
    Returns period for given TR code.
    Period can be one of  'tick', 'min', 'day', 'week', 'month' or 'year'.
    """
    return _tr_code_to_period[tr_code]


def get_record_name_for_code(tr_code):
    return _code_type_to_record_name[_tr_code_to_code_type[tr_code]]


def get_datetime_column(period):
    return _period_to_datetime_column[period]


def get_datetime_format(period):
    return _period_to_datetime_format[period]


def inputs(tr_code, code, unit=None, end=None, prev_next='0'):
    # Copy needed inputs to modify
    inputs = dict(_inputs_for_tr_code[tr_code])

    # To set code with appropriate record name for each TR code
    record_name = get_record_name_for_code(tr_code)  # '종목코드' or '업종코드'
    inputs[record_name] = code

    # To set key, val for each different period
    use_unit = get_tr_code(['tick', 'min'])
    use_date = get_tr_code(['day', 'week', 'month', 'year'])

    if tr_code in use_unit:
        inputs['틱범위'] = str(unit) if unit else '1'
    elif tr_code in use_date:
        # inputs['끝일자'] = str(end) if end else ''  # deprecated
        inputs['기준일자'] = str(end) if end else ''  # cf. 기준일자 = end (not start)
    else:
        raise KeyError(f'Tr_code must be one of opt10079 ~ opt10083.')

    return inputs.items()


def preper(tr_code, otype):
    return ((key, _prep_for_outputs[key]) for key in _outputs_for_tr_code[tr_code][otype])


"""
Protected Variables
  - Instead of directly accessing to these variables, use get methods in this module 
"""
# Map period, code type to matching TR code
_period_to_tr_code = {
    'tick': {
        stock: 'opt10079',
        sector: 'opt20004'
    },
    'min': {
        stock: 'opt10080',
        sector: 'opt20005'
    },
    'day': {
        stock: 'opt10081',
        sector: 'opt20006'
    },
    'week': {
        stock: 'opt10082',
        sector: 'opt20007'
    },
    'month': {
        stock: 'opt10083',
        sector: 'opt20008'
    },
    'year': {
        stock: 'opt10094',
        sector: 'opt20019'
    }
}

# Map TR code to matching period
_tr_code_to_period = {
    tr_code: period for period, tr_dic in _period_to_tr_code.items() for ctype, tr_code in tr_dic.items()
}

# Map TR code to code type
_tr_code_to_code_type = {
    tr_code: ctype for tr_dic in _period_to_tr_code.values() for ctype, tr_code in tr_dic.items()
}

# Map code type to record name to fetch code from downloaded data
_code_type_to_record_name = {
    stock: '종목코드',
    sector: '업종코드'
}

# Datetime column name for each period
_period_to_datetime_column = {
    'tick': '체결시간',
    'min': '체결시간',
    'day': '일자',
    'week': '일자',
    'month': '일자',
    'year': '일자'
}

# Pandas parsing format of datetime column for each period
_period_to_datetime_format = {
    # YYYYMMDDHHMMSS = %Y%m%d%H%M%S
    'tick': '%Y%m%d%H%M%S',
    'min': '%Y%m%d%H%M%S',
    'day': '%Y%m%d',
    'week': '%Y%m%d',
    'month': '%Y%m%d',
    'year': '%Y%m%d'
}

# Inputs needed for each TR code request
_inputs_for_tr_code = {
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

# How to pre-process for each output
_prep_for_outputs = {
    number: [
        '평가손익', '총평가손익금액', '수익률(%)', '총수익률(%)',
        '주문가격', '주문번호', '주문수량',
        '예수금',  '보유수량',
        '매입가', '전일종가', '미체결수량',
        '체결량', '거래량',
        '거래대금'
    ],
    string: [
        '종목번호', '종목코드', '종목명',
        '주문상태', '일자', '체결시간',
        '주문구분'
    ],
    remove_sign: [
        '현재가', '시가', '고가',
        '저가',

    ]
}

# Revert dictionary to be in the form of {'key': function}
_prep_for_outputs = defaultdict(
    lambda: string,
    {val: key for key, vals in _prep_for_outputs.items() for val in vals}
)

# Outputs for each TR code in the form of {'TR code': [[single data], [multi data]]}
_outputs_for_tr_code = {
    'opt10079': [  # 주식틱차트조회요청
        ['종목코드', '마지막틱갯수'],
        [
            '체결시간', '현재가', '시가',
            '고가', '저가', '거래량'
        ]
    ],
    'opt10080': [  # 주식분봉차트조회요청
        ['종목코드'],
        [
            '체결시간', '현재가', '시가',
            '고가', '저가', '거래량'
        ]
    ],
    'opt10081': [  # 주식일봉차트조회요청
        ['종목코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt10082': [  # 주식주봉차트조회요청
        ['종목코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt10083': [  # 주식월봉차트조회요청
        ['종목코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt10094': [  # 주식년봉차트조회요청
        ['종목코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt20001': [  # 업종현재가요청
        [
            '현재가', '시가', '고가',
            '저가', '거래량', '거래대금',
            '등락률', '전일대비', '거래형성종목수',
            '거래형성비율',
        ],
        [
            '시간n', '현재가n', '거래량n',
            '누적거래량n', '등락률n', '전일대비n'
        ]
    ],
    'opt20002': [  # 업종별주가요청
        [],
        [
            '종목코드', '종목명', '현재가',
            '시가', '고가', '저가',
            '현재거래량', '등락률', '전일대비'
        ]
    ],
    'opt20003': [  # 전업종지수요청
        [],
        [
            '종목코드', '종목명', '현재가',
            '전일대비', '등락률', '거래량',
            '비중', '거래대금', '상장종목수'
        ]
    ],
    'opt20004': [  # 업종틱차트조회요청
        ['업종코드'],
        [
            '체결시간', '현재가', '시가',
            '고가', '저가', '거래량'
        ]
    ],
    'opt20005': [  # 업종분봉조회요청
        ['업종코드'],
        [
            '체결시간', '현재가', '시가',
            '고가', '저가', '거래량'
        ]
    ],
    'opt20006': [  # 업종일봉조회요청
        ['업종코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt20007': [  # 업종주봉조회요청
        ['업종코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt20008': [  # 업종월봉조회요청
        ['업종코드'],
        [
            '일자', '현재가', '시가',
            '고가', '저가', '거래량',
            '거래대금'
        ]
    ],
    'opt20009': [  # 업종현재가일별요청
        [
            '현재가', '전일대비', '등락률',
            '거래량', '거래대금', '거래형성종목수',
            '거래형성비율', '시가', '고가',
            '저가'
        ],
        [
            '일자n', '현재가n', '전일대비n',
            '등락률n', '등락률n', '누적거래량n'
        ]
    ],
    'opt20019': [  # 업종년봉조회요청
        ['업종코드'],
        [
            '현재가', '거래량', '일자',
            '시가', '고가', '저가',
            '거래대금', '대업종구분', '소업종구분',
            '종목정보', '전일종가'
        ]
    ],
}