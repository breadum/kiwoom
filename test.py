from PyQt5.QtWidgets import QApplication
from collections import defaultdict
from kiwoom import *

import sys


if __name__ == '__main__':
    # QApplication
    app = QApplication(sys.argv)

    # Login
    bot = Bot()
    bot.login()

    """
    # 참고용
    sectors = {
        '종합(KOSPI)': '001',
        '대형주': '002',
        ...
    }
    """
    sectors = {val: key for key, val in config.SECTORS.items()}

    """
    # 저장용
    dic = {
        'stock1' : ['제조', '금속']
        'stock2' : ['제조', '의료/정밀 기기']
        ...
    }
    """
    dic = defaultdict(list)

    # For KOSPI, KOSDAQ
    for mcode in [0, 10]:
        stocks = bot.stock_list(mcode)

        # For all stocks in each market
        for code in stocks:
            """
            >> bot.api.koa_functions('GetMasterStockInfo', '000020')
            >> info = '시장구분0|거래소; 시장구분1|중형주; 업종구분|의약품|제조;'
            
            # 업종구분이 비어있는 종목도 많다.
            # 업종구분이 여러개인 종목도 많다.
            """

            raw = bot.api.koa_functions("GetMasterStockInfo", code).split(';')
            for data in raw:
                if data == '':
                    continue

                elif '시장구분0' in data:
                    # '시장구분0 | 거래소'
                    # '시장구분0 | 코스닥'
                    # '시장구분0 | 코스닥 | 우량기업'
                    parts = data.split('|')[1:]
                    market = parts[0]

                    if market == '거래소':
                        # '시장구분0 | 거래소'
                        dic[code].append('001')  # 종합(KOSPI)

                    elif market == '코스닥':
                        if len(parts) == 2:
                            # '시장구분0 | 코스닥 |'
                            if parts[-1] == '':
                                dic[code].append('101')  # 종합(KOSDAQ)

                            # '시장구분0 | 코스닥 | 우량기업'
                            # cf) 142 : 코스닥 우량기업
                            else:
                                try:
                                    scode = sectors['코스닥 ' + parts[1]]
                                    dic[code].append(scode)
                                except KeyError:
                                    dic[code].append('101')
                        else:
                            # '시장구분0 | 코스닥'
                            dic[code].append('101')

                else:
                    # '시장구분1 | 소형주 '
                    # '업종구분 | 의약품 | 제조'
                    upjongs = data.split('|')[1:]
                    for upjong in upjongs:
                        if upjong == '':
                            continue

                        # Fix mapping error
                        elif upjong == '오락,문화':
                            upjong = '오락문화'

                        scode = sectors[upjong]
                        dic[code].append(scode)

                    # Remove duplicates
                    if code in dic:
                        dic[code] = list(dict.fromkeys(dic[code]))

    # Done
    print(dic)

    # Save to pickle
    import pickle
    with open('sectors.pkl', 'wb') as file:
        pickle.dump(dic, file, protocol=pickle.HIGHEST_PROTOCOL)

    """
    # Load from pickle
    import pickle
    with open('sectors.pkl',  'rb') as file:
        dic = pickle.load(file)
    """

    # app.exec()