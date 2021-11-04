"""
TR Data 수신에 관한 스크립트

* KOA Studio에서 아래 항목 참조
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > SetInputValue
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData

TR Data는 KOA Studio에서 'TR 목록'에 해당하는 모든 데이터를 말한다. (opt100001 ~ opw20017)
기본적인 데이터 요청 방식과 데이터 수신 방식은 동일하지만 TR code마다 입출력 데이터의 형식만 조금씩 다르다.

OnReceiveTrData 이벤트의 경우 수많은 종류의 TR 데이터를 수신하기에 이벤트에 여러개의 Slot을 연결해야 한다.
이 때 각각의 Slot을 연결하는 기준을 설정해 놓아 요청에 맞는 Slot을 자동으로 호출될 수 있게한다.

- 권장하는 방식 (예시)
CommRqData로 원하는 TR 데이터를 요청할 때 입력하는 인자 중 rq_name은 개발자가 원하는 대로 지정할 수 있다. 
이 때 요청한 데이터를 수신했을 때 OnReceiveTrData 이벤트가 지정했던 rq_name과 함께 호출된다. 

>> Kiwoom.comm_rq_data(self, 'rq_name', tr_code, prev_next, scr_no)
>> Kiwoom.on_receive_tr_data(self, scr_no, 'rq_name', tr_code, record_name, prev_next, *args)
   
(1) 먼저 rq_name을 Slot 연결 시의 기준으로 설정 후 (2) TR Code에 맞는 여러개의 Signal과 Slot을 각각 연결해 준다.
이 때, 특정 TR code에 대해 작업하는 Signal과 Slot 함수 이름을 동일하게 작성하면 코드 관리가 쉬우므로 이를 권장한다. 

>> (1) Kiwoom.set_connect_hook('on_receive_tr_data', 'rq_name')
>> (2) Kiwoom.connect('on_receive_tr_data', signal=bot.balance, slot=server.balance)
>> 두 함수에 관한 자세한 사항은 help() 함수를 이용하면 함수 활용 정보를 얻을 수 있다.  

- 작동원리 (예시)
1. Bot.balance(...) 함수 안에서 self.api.comm_rq_data(..., rq_name='balance') 호출하며 데이터 요청
2. 정상적으로 서버에 연결된 상태라면, 요청에 대한 응답으로 self.api.on_receive_tr_data(..., rq_name='balance') 이벤트 함수가 호출
3. 위에서 해당 이벤트의 rq_name이 'balance'일 때 slot을 Server.balance(...)로 연동해 두었기에 이 함수가 호출됨

이 때 Server.balance(...) 함수가 호출되고, 만일 데이터가 남아있어 (i.e. prev_next='2') 
다시 Signal 함수인 Bot.balance(...) 함수의 요청이 필요하다면 아래와 같이 코드를 작성한다. 
>> fn = Kiwoom.signal('on_receive_tr_data', 'balance')  # 이벤트에 연결된 Signal 함수를 반환
>> fn(..., prev_next='2')  # Signal 함수에 필요한 인자를 넣어 남은 데이터를 요청한다.

기본적으로 다음과 같이 설정되어 있지만 예시를 위해 스크립트를 작성함.
>> Kiwoom.set_connect_hook('on_receive_tr_data', param='rq_name')
>> Kiwoom.set_connect_hook('on_receive_tr_condition', param='condition_name')
>> Kiwoom.set_connect_hook('on_receive_real_condition', param='condition_name')
"""


import sys
from textwrap import dedent

from PyQt5.QtWidgets import QApplication

from kiwoom import Bot, Server
from kiwoom.data.preps import prep
from kiwoom.utils import name


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class MyBot(Bot):
    def __init__(self, server=None):
        """
        Bot 클래스 초기화 함수 (super().__init__(server))

        1) 상속받고 있는 Bot의 부모 클래스 초기화
            - self.server = kiwoom.Server() 초기화
            - self.server 객체와 동일한 Kiwoom(), Share() 인스턴스를 self.api, self.share 변수로 공유

        2) OnEventConnect 발생 시 Server.login 함수가 호출되도록 연동
            - 사실 1)에서 자동으로 동기화 되지만 사용법 설명을 위해 추가

        3) OnReceiveTrData 발생 시 인자로 주어지는 rq_name에 따라 여러가지 slot을 연동할 수 있도록 설정
            - 마찬가지로 1)에서 자동으로 설정되고 이외에 추가 기본설정은 아래와 같다.
            - Kiwoom.set_connect_hook('on_receive_tr_data', param='rq_name')
            - Kiwoom.set_connect_hook('on_receive_tr_condition', param='condition_name')
            - Kiwoom.set_connect_hook('on_receive_real_condition', param='condition_name')
            - Kiwoom.__init__() 함수를 참조하면 확인 할 수 있다.

        4) OnReceiveTrData 발생 시 rq_name이 'deposit'일 때와 'balance'일 때 각각 작성했던 함수들을 연동
            - 연동하지 않으면 이벤트 발생 시 아무 일도 일어나지 않는다.
        """
        # 사용할 변수 초기화
        self.acc = None

        # 1) 상속받는 Bot 클래스 초기화 필수
        # self.api = Kiwoom() 설정됨
        super().__init__(server)

        # 2) OnEventConnect 발생 시 Server.login 함수가 호출되도록 연동
        self.api.connect('on_event_connect', signal=self.login, slot=self.server.login)

        # 3) 이벤트와 Slot 연결 시 기준 인자 설정하기
        # 이벤트 OnReceiveTrData 발생 시 주어진 rq_name 인자값에 따라 slot을 호출하도록 설정
        # 만일 이를 설정하지 않는다면, 하나의 이벤트에는 하나의 slot만 연결가능
        # > help(Kiwoom.set_connect_hook) & Kiwoom.api_arg_spec('on_receive_tr_data')
        self.api.set_connect_hook('on_receive_tr_data', 'rq_name')

        # 4) 이벤트와 Signal, Slot 연결하기
        # OnReceiveTrData 이벤트에 대하여 3)에 의해 특정 rq_name 값에 따라 signal과 slot이 연결됨
        # 연동 시 key 값이 주어지지 않는다면, rq_name은 signal과 slot의 함수 이름 'balance'/'deposit'으로 자동 설정
        # > help(Kiwoom.connect)
        self.api.connect('on_receive_tr_data', signal=self.deposit, slot=self.server.deposit)
        self.api.connect('on_receive_tr_data', signal=self.balance, slot=self.server.balance)

        # 3)과 4) 연결 설정 후에는 다음과 같이 활용할 수 있다.
        # on_receive_tr_data(..., rq_name='balance', ...) 이벤트 수신 시 server.balance 자동 호출됨
        # self.api.signal('on_receive_tr_event', 'balance') 호출 시 bot.balance 함수 핸들 반환
        # self.api.slot('on_receive_tr_event', 'balance') 호출 시 server.balance 함수 핸들 반환

        # * 이벤트가 호출될 때 사용되는 입력 변수 확인하기
        # (1) help(Kiwoom.on_receive_tr_data)
        # (2) Kiwoom.api_arg_spec('on_receive_tr_data')
        # >> ['self', 'scr_no', 'rq_name', 'tr_code', 'record_name', 'prev_next']

        # 참고 가이드
        # 1) print(config.events)  # 이벤트 목록
        # 2) print(Kiwoom.api_arg_spec('on_receive_tr_data'))  # 함수인자 목록
        # 3) help(Kiwoom.connect) and help(Kiwoom.set_connect_hook)  # Doc String

    def account(self):
        """
        튜토리얼 4.Account.py 참고
        """
        cnt = int(self.api.get_login_info('ACCOUNT_CNT'))  # 계좌개수
        accounts = self.api.get_login_info('ACCLIST').split(';')[:cnt]  # 계좌번호

        user_id = self.api.get_login_info('USER_ID')  # 유저아이디
        user_name = self.api.get_login_info('USER_NAME')  # 유저이름

        # 접속 서버 타입
        server = self.api.get_login_info('GetServerGubun')
        server = '모의투자' if server.strip() == '1' else '실서버'

        # 첫번 째 계좌 사용 (거래종목에 따라 확인)
        self.acc = accounts[0]

        return {  # 딕셔너리 리턴
            '계좌개수': cnt,
            '계좌번호': accounts,
            '유저아이디': user_id,
            '유저이름': user_name,
            '서버구분': server
        }

    def deposit(self):
        """
        예수금 정보 요청함수

        * Note
        comm_rq_data 실행 시 올바르게 요청했다면 on_receive_tr_data 함수가 호출된다.

        * KOA Studio 참고 가이드
        1) TR 목록 > opw00001 > INPUT
        2) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > SetInputValue
        3) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
        """
        print('Bot.deposit() 호출')

        # 예수금상세현황요청 TR
        tr_code = 'opw00001'

        # 입력데이터
        inputs = {
            '계좌번호': self.acc,
            '비밀번호': '0000',
            '비밀번호입력매체구분': '00',
            '조회구분': '1'
        }

        # 요청 시 필요한 입력데이터 세팅함수 API 개발가이드
        # help(Kiwoom.set_input_value)
        for key, val in inputs.items():
            self.api.set_input_value(key, val)

        # TR Data 요청함수 API 개발가이드
        # > help(Kiwoom.comm_rq_data)
        # > comm_rq_data(rq_name, tr_code, prev_next, scr_no)
        self.api.comm_rq_data('deposit', tr_code, '0', '0000')

        # [필수] 'on_receive_tr_data' 이벤트가 호출 될 때까지 대기
        self.api.loop()
        print('Bot.deposit() 종료')

    def balance(self, prev_next='0'):
        """
        계좌평가잔고내역 요청함수

        * Note
        comm_rq_data 실행 시 올바르게 요청했다면 on_receive_tr_data 함수가 호출된다.

        * KOA Studion 참고 가이드
        1) TR 목록 > opw00018 > INPUT
        2) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > SetInputValue
        3) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > CommRqData
        """
        print('Bot.balance(prev_next) 호출')

        # 계좌평가잔고내역요청 TR
        tr_code = 'opw00018'

        # 입력데이터
        inputs = {
            '계좌번호': self.acc,
            '비밀번호': '0000',
            '비밀번호입력매체구분': '00',
            '조회구분': '1'
        }

        # 요청 시 필요한 입력데이터 세팅함수 API 개발가이드
        # > help(Kiwoom.set_input_value)
        for key, val in inputs.items():
            self.api.set_input_value(key, val)

        # TR Data 요청함수 API 개발가이드
        # > help(Kiwoom.comm_rq_data)
        # > comm_rq_data(rq_name, tr_code, prev_next, scr_no)
        self.api.comm_rq_data('balance', tr_code, prev_next, '0000')

        # [필수] on_receive_tr_data 이벤트가 호출 될 때까지 대기
        self.api.loop()
        print('Bot.balance(prev_next) 종료')

    def run(self):
        """
        작성했던 코드 실행함수

        1) 로그인
        2) 로그인 상태 확인
        3) 계좌 정보 출력
        """
        # 로그인 요청
        self.login()

        # 접속 성공여부 확인
        if not self.connected():
            raise RuntimeError(f"Server Not Connected.")
            # or you may exit script - import sys; sys.exit()

        # 계좌정보확인 요청
        info = self.account()

        # 예수금 요청
        self.deposit()

        # 계좌잔고 요청
        self.balance()

        # Server Class에서 다운로드된 예수금 정보 출력
        print('\n-- 예수금확인 --')
        print(f"\n예수금 : {format(self.share.get_single('deposit', '예수금'), ',')}원")

        # Server Class에서 다운로드된 잔고 데이터 확인
        print('\n-- 계좌잔고확인 --')
        print(dedent(
            f"""
            Single Data: 
                총수익률(%) = {self.share.get_single('balance', '총수익률(%)')}%
                총평가손익금액 = {self.share.get_single('balance', '총평가손익금액')}원
            """
        ))
        print(f"Multi Data: {self.share.get_multi('balance', key=None)}")

        # ... to be continued


# 서버에서 데이터를 받아 처리하는 클래스 (사용자 작성)
class MyServer(Server):
    def __init__(self):
        """
        Server Class 초기화 함수

        1) Bot Class와 Kiwoom(), Share() 클래스의 인스턴스를 공유한다.
            - self.api, self.share = Kiwoom(), Share()
            - Bot 클래스를 초기화 할 때 공유된다.
            > Bot.__init__(sever=Server())

        2) 사용할 변수들을 초기화 한다.
            - self.downloading
        """
        super().__init__()

        # Bot 클래스를 초기화 할 때 다음 두 변수가 자동 설정됨
        # self.api = Kiwoom()
        # self.share = Share()

        # 사용할 변수
        self.downloading = False

    def deposit(self, _, rq_name, tr_code, __, ___):
        """
        Bot.deposit() 함수로 인해 OnReceiveTrData 이벤트 발생 시 예수금 데이터 처리함수

        * Note
        Bot.deposit 함수에서 comm_rq_data(..., rq_name='deposit', ...) 함수 호출로 인해,
        on_receive_tr_data 이벤트 함수가 호출될 때 이 함수가 호출되도록 한다.  # 319 번째 줄 참고
        >> self.api.connect('on_receive_tr_data', signal=self.signal.deposit, slot=self.slot.deposit)

        * KOA Studio 참고 가이드
        1) TR 목록 > opw00001 > INPUT
        2) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > GetCommData
        3) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData
        """
        print('\tServer.deposit(scr_no, rq_name, tr_code, record_name, prev_next) 호출')

        # 예수금 데이터 저장
        self.share.update_single('deposit', '예수금', int(self.api.get_comm_data(tr_code, rq_name, 0, '예수금')))

        # [필수] 대기중인 코드 실행 (177번째 줄)
        self.api.unloop()
        print('\tServer.deposit(scr_no, rq_name, tr_code, record_name, prev_next) 종료')

    def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):
        """
        Signal.balance() 함수로 인해 OnReceiveTrData 이벤트 발생 시 계좌평가잔고내역 데이터 처리함수

        * Note
        Signal.balance 함수에서 comm_rq_data(..., rq_name='balance', ...) 함수 호출로 인해,
        on_receive_tr_data 이벤트 함수가 호출될 때 이 함수가 호출되도록 한다.  # 98 번째 줄 참고
        >> self.api.connect('on_receive_tr_data', signal=bot.balance, slot=self.server.balance)

        * KOA Studio 참고 가이드
        1) TR 목록 > opw00018 > INPUT
        2) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > GetCommData
        3) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > GetRepeatCnt
        3) 개발가이드 > 조회와 실시간데이터처리 > 관련함수 > OnReceiveTrData
        """
        print('\tServer.balance(scr_no, rq_name, tr_code, record_name, prev_next) 호출')

        # TR 데이터 수신 API 개발가이드
        # help(Kiwoom.on_receive_tr_data)

        # 다운로드 시작을 위한 변수 초기화
        if not self.downloading:
            self.downloading = True

        # 멀티데이터 저장
        keys = ['종목번호', '종목명', '평가손익', '수익률(%)', '보유수량', '매입가', '현재가']
        data = {key: list() for key in keys}
        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
        for i in range(cnt):
            for key in keys:
                val = prep(self.api.get_comm_data(tr_code, rq_name, i, key))
                data[key].append(val)

        # 봇 인스턴스와 데이터 공유
        for key in keys:
            self.share.extend_multi('balance', key, data[key])

        # 만일, 데이터가 더 있다면 signal 함수 한번 더 호출 (종목 수 25개 이상인 경우)
        if prev_next == '2':
            fn = self.api.signal('on_receive_tr_data', 'balance')
            fn(prev_next)  # call signal function again to receive remaining data

        # 요청 할 데이터가 더 없는 경우
        else:
            # Single 데이터 저장
            for key in ['총평가손익금액', '총수익률(%)']:
                val = prep(self.api.get_comm_data(tr_code, rq_name, 0, key))
                self.share.update_single(name(), key, val)  # name() = 'balance'

            # 다운로드 완료
            self.downloading = False
            self.api.unloop()  # 216번 째 줄 실행
            print('\tServer.balance(scr_no, rq_name, tr_code, record_name, prev_next) 종료')


# 실행 스크립트
if __name__ == '__main__':

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = MyBot(MyServer())

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

Bot.deposit() 호출
	Server.deposit(scr_no, rq_name, tr_code, record_name, prev_next) 호출
	Server.deposit(scr_no, rq_name, tr_code, record_name, prev_next) 종료
Bot.deposit() 종료
Bot.balance(prev_next) 호출
	Server.balance(scr_no, rq_name, tr_code, record_name, prev_next) 호출
	Server.balance(scr_no, rq_name, tr_code, record_name, prev_next) 종료
Bot.balance(prev_next) 종료

-- 예수금확인 --

예수금 : 497,717,210원

-- 계좌잔고확인 --

Single Data:
    총수익률(%): 77.77%
    총평가손익금액': 1234567원

Multi Data: defaultdict(<class 'list'>,{
    '종목번호': ['A058820'], '종목명': ['CMG제약'], '평가손익': [1234567], 
    '수익률(%)': [77.7], '보유수량': [777], '매입가': [3333], '현재가': [7777]
})
"""
