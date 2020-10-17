from PyQt5.QtWidgets import QApplication
from collections import defaultdict
from kiwoom import *

import sys


"""
TR Data 수신에 관한 스크립트로 KOA Studio에서 아래 항목 참조
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData

TR Data는 KOA Studio에서 'TR 목록'에 해당하는 모든 데이터를 말한다. (opt100001 ~ opw20017)
기본적인 데이터 요청 방식과 데이터 수신 방식은 동일하지만 TR code마다 입출력 데이터의 형식만 조금씩 다르다.
"""

# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api

    def login(self):
        # 서버에 접속 요청
        self.api.comm_connect()
        # [필수] 로그인 될 때까지 대기
        self.api.loop()

    def is_connected(self):
        # 0 (연결안됨), 1 (연결됨)
        state = self.api.get_connect_state()

        if state == 1:
            return True  # 연결된 경우
        return False  # 연결되지 않은 경우

    def account(self):
        cnt = int(self.api.get_login_info('ACCOUNT_CNT'))  # 계좌개수
        accounts = self.api.get_login_info('ACCLIST').split(';')[:cnt]  # 계좌번호

        user_id = self.api.get_login_info('USER_ID')  # 유저아이디
        user_name = self.api.get_login_info('USER_NAME')  # 유저이름

        # 접속 서버 타입
        server = int(self.api.get_login_info('GetServerGubun'))
        server = '실서버' if server != 1 else '모의투자'

        return {  # 딕셔너리 리턴
            '계좌개수': cnt,
            '계좌번호': accounts,
            '유저아이디': user_id,
            '유저이름': user_name,
            '서버구분': server
        }

    def balance(self, prev_next='0'):
        """

        :param prev_next:
        :return:
        """
        # 계좌평가잔고내역요청 TR
        tr_code = 'opw00018'

        # 계좌번호 - 더 좋은 방식으로 얼마든지 구현가능
        account = self.account()['계좌번호'][0]

        # 입력데이터
        inputs = {
            '계좌번호': account,
            '비밀번호': '0000',
            '비밀번호입력매체구분': '00',
            '조회구분': '1'
        }

        # 요청 시 필요한 입력데이터 세팅함수 API 개발가이드
        # help(Kiwoom.set_input_value)

        for key, val in inputs.items():
            self.api.set_input_value(key, val)

        # TR Data 요청함수 API 개발가이드
        # help(Kiwoom.comm_rq_data)

        # args: rq_name, tr_code, prev_next, scr_no
        self.api.comm_rq_data('balance', tr_code, prev_next, '0000')

        # [필수] 데이터가 수신될 때까지 대기
        self.api.loop()


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api
        self.is_downloading = False
        self.data = dict() # defaultdict(list)

    def login(self, err_code):
        # err_code와 그에 해당하는 메세지
        emsg = config.error.err_msg(err_code)
        # 로그인 성공/실패 출력
        print(f'로그인 {emsg}')
        # [필수] 대기중인 코드 실행
        self.api.unloop()

    def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):
        """

        :param scr_no:
        :param rq_name:
        :param tr_code:
        :param record_name:
        :param prev_next:
        :return:
        """
        print('Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next) 호출')

        # f
        # help(Kiwoom.on_receive_tr_data)

        # To initiate downloading and saving data
        if not self.is_downloading:
            self.data['balance']['single'] = dict()
            self.data['balance']['multi'] = defaultdict(list)
            self.is_downloading = True

        # 멀티데이타 저장
        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
        for i in range(cnt):
            for key in ['종목번호', '종목명', '평가손익', '수익률(%)', '보유수량', '매입가', '현재가']:
                self.data['balance']['multi'][key].append(
                    str.strip(  # or int(), float()
                        self.api.get_comm_data(tr_code, rq_name, i, key)
                    )
                )

        # 만일, 데이터가 더 있다면 signal 함수 한번 더 호출
        if prev_next == '2':
            fn = self.api.signal('balance')  # or self.api.signal(rq_name)
            fn(prev_next)  # call signal function again to receive remaining data

        else:
            # To fetch single data
            for key in ['총평가손익금액', '총수익률(%)']:
                self.data['balance']['single'][key].append(
                    float(self.api.get_comm_data(tr_code, rq_name, 0, key))
                )

            # Downloading completed
            self.is_downloading = False
            self.api.unloop()
            print('Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next) 종료')


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        self.api.connect(slot=self.slot.login, event='on_event_connect')
        self.api.connect(signal=self.signal.balance, slot=self.slot.balance)

    def run(self):
        # 로그인 요청
        self.signal.login()

        # 접속 성공여부 확인
        if self.api.get_connect_state() != 1:
            raise RuntimeError(f"Server not connected.")
            # or you may exit script - import sys; sys.exit()

        # 계좌잔고요청
        self.signal.balance()

        # 다운로드된 잔고 데이터 확인
        print(self.slot.data['balance'])

        # ... to be continued


# 실행 스크립트
if __name__ == '__main__':

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = Bot()

    # 로그인
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()
