from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


"""
로그인과 버전처리에 대한 예제 스크립트로 KOA Studio에서 아래 항목 참조

개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect
개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState
개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo
"""


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        """
        :param api : Kiwoom() 인스턴스
        """
        self.api = api

    def login(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect 참조
        comm_connect 실행 시 on_connect_event 함수가 호출된다.
        """
        print('Signal.login() 호출')

        # 연결 요청 API 가이드
        # help(Kiwoom.comm_connect)

        # 서버에 접속 요청
        self.api.comm_connect()

        # [필수] 로그인 될 때까지 대기
        self.api.loop()

        print('Signal.login() 종료')

    def is_connected(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState 참조
        :return: 연결상태 확인 후 연결되어 있다면 True, 그렇지 않다면 False
        """
        # 현재 접속상태 표시 API 가이드
        # help(Kiwoom.get_connect_state)
        # 0 (연결안됨), 1 (연결됨)

        state = self.api.get_connect_state()
        print(f'현재 접속상태 = {state}')

        if state == 1:
            return True  # 연결된 경우
        return False  # 연결되지 않은 경우


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        """
        :param api : Kiwoom() 인스턴스
        """
        self.api = api

    def login(self, err_code):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > OnEventConnect 참조
        comm_connect 실행 시 on_event_connect 함수가 호출될 때 이 함수가 호출되도록 한다.
        >> self.api.connect(slot=self.slot.login, event='on_event_connect')  # 102번째 줄 참고
        """
        print('Slot.login(err_code) 호출')

        # 접속 요청 시 발생하는 이벤트 API 가이드
        # help(Kiwoom.on_event_connect)

        # 에러 메세지 출력 함수 가이드
        # help(kiwoom.config.error.err_msg)

        # err_code와 그에 해당하는 메세지
        emsg = config.error.err_msg(err_code)

        # 로그인 성공/실패 출력
        print(f'로그인 {emsg}')

        # [필수] 대기중인 코드 실행
        self.api.unloop()

        print('Slot.login(err_code) 종료')


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # 이벤트 발생 시 함수 자동호출을 위한 연결함수 가이드
        # help(Kiwoom.connect)
        self.api.connect(slot=self.slot.login, event='on_event_connect')

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