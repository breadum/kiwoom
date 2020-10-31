from PyQt5.QtWidgets import QApplication
from collections import defaultdict
from kiwoom import *

import sys


"""
TR Data 수신에 관한 스크립트로 KOA Studio에서 아래 항목 참조
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > SetInputValue
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData

TR Data는 KOA Studio에서 'TR 목록'에 해당하는 모든 데이터를 말한다. (opt100001 ~ opw20017)
기본적인 데이터 요청 방식과 데이터 수신 방식은 동일하지만 TR code마다 입출력 데이터의 형식만 조금씩 다르다.

OnReceiveTrData 이벤트의 경우 수많은 종류의 TR 데이터를 수신하기에 이벤트에 여러개의 Slot을 연결해야 한다.
이 때 각각의 Slot을 연결하는 기준을 설정해 놓아 요청에 맞는 Slot을 자동으로 호출될 수 있게한다.

- 권장하는 방식 (예시)
CommRqData로 원하는 TR 데이터를 요청할 때 입력 인자 중 rq_name은 개발자가 원하는 대로 설정할 수 있다. 
이 때 요청한 데이터를 수신했을 때 OnReceiveTrData 이벤트가 설정했던 rq_name과 함께 호출된다. 

>> Kiwoom.comm_rq_data(self, 'rq_name', tr_code, prev_next, scr_no)
>> Kiwoom.on_receive_tr_data(self, scr_no, 'rq_name', tr_code, record_name, prev_next, *args)
   
(1) 먼저 rq_name을 Slot 연결 시의 기준으로 설정 후 (2) Signal과 Slot을 연결해 준다.
이 때, 특정 TR code에 대해 작업하는 Signal과 Slot 함수 이름은 동일하게 작성하면 코드 관리가 쉬우므로 권장한다. 

>> (1) Kiwoom.set_connect_hook('on_receive_tr_data', 'rq_name')
>> (2) Kiwoom.connect('on_receive_tr_data', signal=signal.balance, slot=slot.balance)
>> 두 함수에 관한 자세한 사항은 help() 함수를 이용하면 함수 활용 정보를 얻을 수 있다.  

- 작동원리 (예시)
1. Signal.balance(...) 함수 안에서 self.api.comm_rq_data(..., rq_name='balance') 호출하며 데이터 요청
2. 정상적으로 서버에 연결된 상태라면, 요청에 대한 응답으로 Kiwoom.on_receive_tr_data(..., rq_name='balance') 이벤트 함수가 호출
3. 위에서 해당 이벤트의 rq_name이 'balance'일 때 Slot을 연결해 두었기 때문에 Slot.balance(...) 함수가 동일한 입력값으로 호출됨

참고) 이 때 Slot.balance(...) 함수가 호출되었는데 데이터가 남아있어 다시 Signal 함수 요청이 필요하다면
>> balance_signal = Kiwoom.signal('on_receive_tr_data', 'balance')  # 이벤트에 연결된 Signal 함수를 반환
>> balance_signal(..., prev_next='2')  # Signal 함수에 인자를 넣어 남은 데이터를 요청한다.

기본적으로 다음과 같이 설정되어 있지만 예시를 위해 스크립트를 작성함.
>> Kiwoom.set_connect_hook('on_receive_tr_data', arg='rq_name')
>> Kiwoom.set_connect_hook('on_receive_tr_condition', arg='condition_name')
>> Kiwoom.set_connect_hook('on_receive_real_condition', arg='condition_name')
"""


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api

    def login(self):
        # 서버에 접속 요청
        self.api.comm_connect()
        # [필수] 이벤트가 호출 될 때까지 대기 (on_event_connect)
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
        server = '모의투자' if server == 1 else '실서버'

        return {  # 딕셔너리 리턴
            '계좌개수': cnt,
            '계좌번호': accounts,
            '유저아이디': user_id,
            '유저이름': user_name,
            '서버구분': server
        }

    def balance(self, prev_next='0'):
        """
        계좌평가잔고내역 요청을 위한 함수
        개발가이드 > 조회와 실시간데이터처리 > 관련함수 > SetInputValue
        개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
        comm_rq_data 실행 시 올바르게 요청했다면 on_receive_tr_data 함수가 호출된다.
        """
        print('Signal.balance(scr_no, rq_name, tr_code, record_name, prev_next) 호출')

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

        # [필수] on_receive_tr_data 이벤트가 호출 될 때까지 대기
        self.api.loop()
        print('Signal.balance(scr_no, rq_name, tr_code, record_name, prev_next) 종료')


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api
        self.is_downloading = False
        self.data = dict()  # defaultdict(list)

    def login(self, err_code):
        # err_code에 해당하는 메세지
        emsg = config.error.msg(err_code)
        # 로그인 성공/실패 출력
        print(f'Login ({emsg})')
        # [필수] 대기중인 코드 실행 (59번째 줄)
        self.api.unloop()

    def balance(self, scr_no, rq_name, tr_code, record_name, prev_next, *args):
        """
        on_receive_tr_data 이벤트가 호출될 때 이 함수에서 처리할 수 있도록 구현한다.
        개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData
        """
        print('\tSlot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 호출')

        # TR 데이터 수신 API 개발가이드
        # help(Kiwoom.on_receive_tr_data)

        # 다운로드 시작을 위한 변수 초기화
        if not self.is_downloading:
            self.data['balance'] = {
                'single': dict(),
                'multi': defaultdict(list)
            }
            self.is_downloading = True

        # 데이터 전처리 함수 예시
        def prep(x):
            """
            데이터 전처리 Type Casting 시도 우선순위
            int 변환 -> float 변환 -> string 변환
            :param x: raw data from the server
            :return: type-casted data
            """
            try: return int(x)
            except ValueError: pass
            try: return float(x)
            except ValueError: pass
            return str.strip(x)

        # 멀티데이터 저장
        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
        for i in range(cnt):
            for key in ['종목번호', '종목명', '평가손익', '수익률(%)', '보유수량', '매입가', '현재가']:
                self.data['balance']['multi'][key].append(
                    prep(self.api.get_comm_data(tr_code, rq_name, i, key))
                )

        # 만일, 데이터가 더 있다면 signal 함수 한번 더 호출 (종목 수 25개 이상인 경우)
        if prev_next == '2':
            fn = self.api.signal('balance')  # or self.api.signal(rq_name)
            fn(prev_next)  # call signal function again to receive remaining data

        # 요청 할 데이터가 더 없는 경우
        else:
            # Single 데이터 저장
            for key in ['총평가손익금액', '총수익률(%)']:
                self.data['balance']['single'][key] \
                    = prep(self.api.get_comm_data(tr_code, rq_name, 0, key))

            # 다운로드 완료
            self.is_downloading = False
            self.api.unloop()  # 119번 째 줄 실행
            print('\tSlot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 종료')


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # 0. 이벤트 호출될 때 사용되는 입력 변수 확인하기
        # (1) help(Kiwoom.on_receive_tr_data)
        # (2) self.api.api_arg_spec('on_receive_tr_data')
        # >> ['self', 'scr_no', 'rq_name', 'tr_code', 'record_name', 'prev_next']

        # 1. 이벤트와 Slot 연결 시 기준 인자(hook) 설정하기
        # OnReceiveTrData 이벤트의 경우 많은 종류의 TR 데이터를 처리해야 하므로
        # 각각의 TR 요청에 대해 처리할 수 있도록 여러개의 Slot을 연결할 필요가 있다.
        # 이때 사용자 입력으로 주어지는 값(hook)에 따라 정해진 Slot이 호출될 수 있도록 한다.
        # 아래 예시에서는 rq_name에 주어지는 값에 따라 정해진 Slot이 호출되도록 한다.
        # help(Kiwoom.set_connect_hook)
        self.api.set_connect_hook('on_receive_tr_data', 'rq_name')

        # 2. 이벤트와 Signal, Slot 연결하기
        # OnReceiveTrData 이벤트와 Signal, Slot이 연결되도록 한다.
        # Signal, Slot 함수 이름이 같도록 구현하면 rq_name='balance'일 때 자동으로 연결된다.
        # 만일 그렇지 않다면, key='balance'라는 키워드 인자를 추가해서 connect 함수를 호출한다.
        # help(Kiwoom.connect)
        self.api.connect('on_receive_tr_data', signal=self.signal.balance, slot=self.slot.balance)

        # 로그인 이벤트와 Signal, Slot 연결
        self.api.connect('on_event_connect', signal=self.signal.login, slot=self.slot.login)

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
        print('\n-- 계좌잔고확인 --')
        print(f"Single Data: {self.slot.data['balance']['single']}")
        print(f"Multi Data: {self.slot.data['balance']['multi']}")

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


"""
기본적으로 on_receive_msg 이벤트가 처리되도록 구현되어 있어, 
중간에 계좌 조회 시 해당 이벤트로 인해 아래와 같은 메세지가 보일 수 있다. 

>> 화면번호: 0000, 요청이름: balance, TR코드: opw00018
>> [00Z310] 모의투자 조회가 완료되었습니다

메세지가 보이거나/보이지 않도록 하려면 다음 함수를 활용하면 된다.
>> Kiwoom.message(True)
>> Kiwoom.message(False)

[실행결과]
Login (Error - Code: 0, Type: OP_ERR_NONE, Msg: 정상처리)
Signal.balance(scr_no, rq_name, tr_code, record_name, prev_next) 호출
    Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 호출
    Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 종료
Signal.balance(scr_no, rq_name, tr_code, record_name, prev_next) 종료

-- 계좌잔고확인 --
Single Data: {
    '총평가손익금액': 1234567, 
    '총수익률(%)': 77.7
}
Multi Data: defaultdict(<class 'list'>,{
    '종목번호': ['A058820'], '종목명': ['CMG제약'], '평가손익': [1234567], 
    '수익률(%)': [77.7], '보유수량': [777], '매입가': [3333], '현재가': [7777]
})
"""
