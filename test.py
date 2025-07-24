"""
Test for new updates.
"""
import sys

from PyQt5.QtWidgets import QApplication

from kiwoom import Bot, Server
from kiwoom.data.preps import prep
from kiwoom.utils import name


# class Bot(Bot):
#     def __init__(self, server):
#         super().__init__(server)
#         self.acc = None
#         self.api.set_connect_hook('on_receive_tr_data', 'rq_name')
#         self.api.connect('on_receive_tr_data', signal=self.balance, slot=self.server.balance)
#         self.api.connect('on_receive_tr_data', signal=self.trade, slot=self.server.trade)
#         self.api.connect('on_receive_chejan_data', slot=self.server.chejan)  # without hook

#     def account(self):
#         cnt = int(self.api.get_login_info('ACCOUNT_CNT'))  # 계좌개수
#         accounts = self.api.get_login_info('ACCLIST').split(';')[:cnt]  # 계좌번호
#         self.acc = accounts[0]

#     # Single and Multi Data
#     def balance(self, prev_next='0'):
#         tr_code = 'opw00018'
#         inputs = {
#             '계좌번호': self.acc,
#             '비밀번호': '',
#             '비밀번호입력매체구분': '00',
#             '조회구분': '1'
#         }
#         for key, val in inputs.items():
#             self.api.set_input_value(key, val)
        
#         return_code = self.api.comm_rq_data('balance', tr_code, prev_next, '0000')
#         if return_code == 0:
#             self.api.loop()

#     # Send orders of futures and options
#     def trade(self):
#         """
#         실계좌일 경우 종목코드 입력하지 마세요.
#         어떠한 경우에도 손실 책임지지 않습니다.
#         """
#         inputs = (
#             'trade',     # rq_name
#             '0000',      # 화면번호
#             self.acc,    # 계좌번호
#             '------',    # 입력금지!! (종목코드)
#             1,           # 신규매매 (주문종류)
#             2,           # Long (매매구분)
#             3,           # 시장가 (거래구분)
#             10,          # 주문수량
#             '0',         # 주문가격
#             '',          # 원주문번호
#         )
#         if self.api.get_login_info('GetServerGubun') != 1:
#             print('실제 계좌이므로 주문하지 않습니다.')
#             return

#         if self.api.send_order_fo(*inputs) == 0:
#             self.api.loop()
#         else:
#             # Do something to handle error
#             raise RuntimeError(f'Sending order went wrong.')


# class Server(Server):
#     def __init__(self):
#         super().__init__()
#         self.downloading = False

#     def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):
#         if not self.downloading:
#             self.downloading = True

#         keys = ['종목번호', '종목명', '평가손익', '수익률(%)', '보유수량', '매입가', '현재가']
#         data = {key: list() for key in keys}
#         cnt = self.api.get_repeat_cnt(tr_code, rq_name)
#         for i in range(cnt):
#             for key in keys:
#                 val = prep(self.api.get_comm_data(tr_code, rq_name, i, key))
#                 data[key].append(val)

#         # Multi Data
#         for key in keys:
#             self.share.extend_multi('balance', key, data[key])

#         if prev_next == '2':
#             fn = self.api.signal('on_receive_tr_data', 'balance')
#             fn(prev_next)
#         else:
#             # Single Data
#             for key in ['총평가손익금액', '총수익률(%)']:
#                 val = prep(self.api.get_comm_data(tr_code, rq_name, 0, key))
#                 self.share.update_single(name(), key, val)  # name() = 'balance'

#             self.downloading = False
#             self.api.unloop() 

#     # Mapped by hook, if rq_name='trade' when on_receive_tr_data() is called.
#     def trade(self, scr_no, rq_name, tr_code, record_name, prev_next):
#         num = self.api.get_comm_data(tr_code, rq_name, 0, '주문번호').strip()
#         if num == '':
#             self.api.unloop()
#             raise RuntimeError('Executing order failed.')
        
#         # Order filled.
#         pass

#     # Mapped directly from on_receive_chejan_data() without hook.
#     def chejan(self, gubun, item_cnt, fid_list):
#         # Only for Python >= 3.10.4.
#         # Use if / elif / else, otherwise.
#         match gubun:
#             case '0':  # 접수/체결
#                 pass
#             case '1':  # 잔고변경
#                 pass
#             case '4':  # 파생잔고변경
#                 pass
#             case _:
#                 raise RuntimeError('Execution went wrong.')

#         # cf. 9203 : 주문번호
#         for fid in fid_list:
#             self.api.get_chejan_data(fid)
        
#         # Don't forget to self.api.unloop() somewhere.
#         pass
# class Bot(Bot):
#     def sectors(self, market_gubun):
#         codes, names = list(), list()
#         sectors = self.api.koa_functions('GetUpjongCode', market_gubun)
#         for sector in sectors.split('|')[:-1]:
#             data = sector.split(',')
#             codes.append(data[1])
#             names.append(data[2])
#         return codes, names

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     bot = Bot()
#     bot.login()
#     for market in ('0', '1', '2', '4', '7'):
#         print(bot.sector_list(market))       


# 실행 스크립트
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     bot = Bot()
#     bot.login()
    
#     from kiwoom.config.const import MARKET_GUBUNS
#     for market in MARKET_GUBUNS:
#         print(bot.sectors(market))

    # app = QApplication(sys.argv)
    # bot = Bot(Server())
    # bot.login()
    # bot.account()_lit
    # bot.balance()

    # """
    # Check and get single/multi data
    #     * Two different styles.
    #     * Must handle error on your own.
    # """
    # # All single data for balance
    # if bot.share.isin_single('balance'):
    #     print(bot.share.get_single('balance'))  # dict 
    # # Specific single data for balance
    # if bot.share.isin_single('balance', key='총평가손익금액'):
    #     print(bot.share.get_single('balance', key='총평가손익금액'))  # int
    
    # # All multi data for balance
    # try:
    #     bot.share.get_multi('balance')  # dict
    # except KeyError:
    #     pass
    # # Specific multi data for balance
    # try:
    #     print(bot.share.get_multi('balance', key='종목명'))  # list[str]
    # except KeyError:
    #     pass
    
    # """
    # Send orders.
    # """
    # bot.trade()

    # """
    # Interactive mode like jupyter notebook for testing further.
    # """
    # from IPython import embed
    # print("\nType 'exit()' if you want to quit.\n")
    # embed()

    # """
    # Keep connection to kiwwom serverr.
    # """
    # app.exec()


from time import sleep
from PyQt5.QtWidgets import QApplication
from kiwoom import Bot, Server

class Server(Server):
    def on_receive_real_data(self, code, real_type, _):
        if real_type == '주식체결':
            prc = self.api.get_comm_real_data(code, 10)
            # self.share.extend_multi('real_price', code, prc)  # 현재가 list
            self.share.update_single('real_price', code, prc)  # 현재가

class Bot(Bot):
    def register(self, codes):
        self.api.set_real_reg(
            scr_no='2000',
            code_list=codes,
            fid_list='10',
            opt_type='0'
        )

    def real_price(self, code):
        try:
            # return self.share.get_multi('real_price', code)  # 현재가 list 
            return self.share.get_single('real_price', code)  # 현재가
        except KeyError:
            return f'현재가 데이터를 수신하지 못했습니다. : {code} '

    def run(self):
        self.login()
        self.register('005930;005380')
        for i in range(5):
            print(bot.real_price('005930'))
            print(bot.real_price('005380'))
            sleep(3)
        
if __name__ == '__main__':
    app = QApplication([])
    bot = Bot(Server())
    bot.run()