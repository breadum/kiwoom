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
        로그인 요청함수

        * Note
        comm_connect 실행 시 on_connect_event 함수가 호출된다.

        * KOA Studio 참고 가이드
        개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect 참조
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
        로그인 상태확인 요청함수

        * Note
        GetConnectState 반환 값이 '0'이면 연결안됨, '1'이면 연결됨.

        * KOA Studio 참고 가이드
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
        Signal.login() 함수로 인해 OnEventConnect 이벤트 발생 시 로그인 메세지 처리함수

        * Note
        comm_connect 실행 결과로 on_event_connect 이벤트 함수가 호출될 때 이 함수가 호출되도록 한다.
        >> self.api.connect(slot=self.slot.login, event='on_event_connect')  # 122 번째 줄 참고

        * KOA Studio 참고 가이드
        개발가이드 > 로그인 버전처리 > 관련함수 > OnEventConnect 참조
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

        # [필수] 이벤트를 기다리며 대기중이었던 코드 실행 (42번째 줄)
        self.api.unloop()

        print('\t\tSlot.login(err_code) 종료')


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        """
        Bot 인스턴스 초기화 함수

        1) Kiwoom 인스턴스 생성 후 Signal과 Slot 생성 시 입력값으로 넣어준다.
        2) OnEventConnect 발생 시 Slot.login 함수가 호출되도록 연동해준다.
        """
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Server(self.api)

        # Signal 클래스에서 comm_connect 요청 후 서버에서 응답이 오면 on_event_connect가 호출된다.
        # Kiwoom.on_event_connect(...)가 호출되면 slot.login(...)이 호출될 수 있도록 연결해 준다.
        # help(Kiwoom.connect)
        self.api.connect('on_event_connect', signal=self.signal.login, slot=self.slot.login)

    def run(self):
        """
        작성했던 코드 실행함수

        1) 로그인
        2) 로그인 상태 확인
        """
        print('Bot.run() 호출')

        # 로그인 요청
        self.signal.login()

        # 접속 성공여부 확인
        if not self.signal.is_connected():
            raise RuntimeError(f'Server NOT connected.')
            # or you may exit script - import sys; sys.exit()

        # ... to be continued
        print('Bot.run() 종료')


# 실행 스크립트
if __name__ == '__main__':
    """
    >> python3 2.Login.py 명령을 통해 실행하거나 IDE를 통해 직접 실행해볼 수 있다. 
    """

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
