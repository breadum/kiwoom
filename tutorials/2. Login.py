from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


"""
로그인과 버전처리에 대한 예제 스크립트로 KOA Studio에서 아래 항목 참조

개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect
개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState
개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo

실제로 login 함수는 구현되어 있지만 튜토리얼을 위해 예시로 작성했다.
"""


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    def login(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect 참조
        comm_connect 실행 시 on_connect_event 함수가 호출된다.
        """
        print('\tSignal.login() 호출')

        # 연결 요청 API 가이드
        # help(Kiwoom.comm_connect)

        # 서버에 접속 요청
        self.api.comm_connect()

        # [필수] 이벤트가 호출될 때까지 대기 (on_event_connect)
        self.api.loop()

        print('\tSignal.login() 종료')

    def is_connected(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState 참조
        :return: 연결상태 확인 후 연결되어 있다면 True, 그렇지 않다면 False
        """
        # 현재 접속상태 표시 API 가이드
        # help(Kiwoom.get_connect_state)
        # 0 (연결안됨), 1 (연결됨)

        state = self.api.get_connect_state()
        print(f'\t현재 접속상태 = {state}')

        if state == 1:
            return True  # 연결된 경우
        return False  # 연결되지 않은 경우


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    def login(self, err_code):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > OnEventConnect 참조
        comm_connect 실행 결과로 on_event_connect 이벤트 함수가 호출될 때 이 함수가 호출되도록 한다.
        >> self.api.connect(slot=self.slot.login, event='on_event_connect')  # 98번째 줄 참고
        """
        print('\t\tSlot.login(err_code) 호출')

        # 접속 요청 시 발생하는 이벤트 API 가이드
        # help(Kiwoom.on_event_connect)

        # 에러 메세지 출력 함수 가이드
        # help(kiwoom.config.error.msg)

        # err_code에 해당하는 메세지
        emsg = config.error.msg(err_code)

        # 로그인 성공/실패 출력
        print(f'\t\tLogin ({emsg})')

        # [필수] 이벤트를 기다리며 대기중이었던 코드 실행 (37번째 줄)
        self.api.unloop()

        print('\t\tSlot.login(err_code) 종료')


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # 이벤트 발생 시 함수 자동호출을 위한 연결함수 가이드
        # help(Kiwoom.connect)
        self.api.connect('on_event_connect', signal=self.signal.login, slot=self.slot.login)

    def run(self):
        print('Bot.run() 호출')
        self.signal.login()

        if not self.signal.is_connected():
            raise RuntimeError(f'Server is not connected.')

        # ... to be continued
        print('Bot.run() 종료')


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
Bot.run() 호출
    Signal.login() 호출
        Slot.login(err_code) 호출
        Login (Error - Code: 0, Type: OP_ERR_NONE, Msg: 정상처리)
        Slot.login(err_code) 종료
    Signal.login() 종료
    현재 접속상태 = 1
Bot.run() 종료
"""
