from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


"""
로그인 후 유저 및 서버에 대한 정보 확인 예제 스크립트로 KOA Studio에서 아래 항목 참조

개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo
"""


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    def login(self):
        # 서버에 접속 요청
        self.api.comm_connect()
        # [필수] 이벤트가 호출될 때까지 대기 (on_event_connect)
        self.api.loop()

    def is_connected(self):
        # 0 (연결안됨), 1 (연결됨)
        state = self.api.get_connect_state()

        if state == 1:
            return True  # 연결된 경우
        return False  # 연결되지 않은 경우

    def account(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo 참조
        get_login_info 함수는 이벤트를 거치지 않고 즉시 요청값을 반환해주기 때문에 api.loop() 함수가 필요없다.
        """
        # 로그인 계좌 정보확인 API 개발가이드
        # help(Kiwoom.get_login_info)

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


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    def login(self, err_code):
        # err_code에 해당하는 메세지
        emsg = config.error.msg(err_code)
        # 로그인 성공/실패 출력
        print(f'Login ({emsg})\n')
        # [필수] 대기중인 코드 실행 (23번째 줄)
        self.api.unloop()


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # Signal 클래스에서 comm_connect 요청 후 서버에서 응답이 오면 on_event_connect가 호출된다.
        # Kiwoom.on_event_connect(...)가 호출되면 slot.login(...)이 호출될 수 있도록 연결해 준다.
        self.api.connect('on_event_connect', signal=self.signal.login, slot=self.slot.login)

    def run(self):
        # 로그인 요청
        self.signal.login()

        # 접속 성공여부 확인
        if not self.signal.is_connected():
            raise RuntimeError(f"Server not connected.")
            # or you may exit script - import sys; sys.exit()

        # 계좌 정보 출력
        account = self.signal.account()
        print('-- 계좌 정보 --')
        for key, val in account.items():
            print(f'{key}: {val}')

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
[실행결과]
Login (Error - Code: 0, Type: OP_ERR_NONE, Msg: 정상처리)

-- 계좌 정보 --
계좌개수: 2
계좌번호: ['xxxxxxxxxx', 'xxxxxxxxxx']
유저아이디: breadum
유저이름: ㅇㅇㅇ
서버구분: 모의투자
"""
