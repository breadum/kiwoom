from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


"""
키움증권 Open API+ 활용을 위한 기본적인 Class 구성

1. API를 Python에서 활용할 수 있게 해주는 Kiwoom Class
2. 서버에 데이터를 요청하는 Signal Class (사용자 정의)
3. 요청한 데이터를 처리하는 Slot Class (사용자 정의)
4. Signal과 Slot을 통해 트레이딩 전략을 구현하는 Bot Class (사용자 정의)

API와 사용자 정의 함수들을 연결해 활용할 수 있게 해주는 필수함수

1. Kiwoom.connect(event, signal, slot)
2. Kiwoom.set_connect_hook(event, arg)

구현에 도움을 주는 가이드

1. help(...) 내장함수
2. KOA Studio 개발가이드
3. 키움증권 Open API 고객문의 게시판
"""


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    # ex) 로그인을 요청하는 함수
    def login(self):
        pass


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api  # Kiwoom 인스턴스

    # ex) 서버로 부터 로그인 응답을 받았을 때 처리하는 함수
    def login(self):
        pass


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
        self.slot = Slot(self.api)

        # ex) Signal, Slot, Event 연결
        # 1) 로그인 시 아래 이벤트가 호출된다. (KOA Studio 개발가이드 참조)
        event = 'on_event_connect'
        # 2) 해당 이벤트 호출 시 slot.login(*args, **kwargs) 함수가 자동호출 되도록 설정
        self.api.connect(event, signal=self.signal.login, slot=self.slot.login)

    # 봇 작동시작
    def run(self):
        """
        작성했던 코드 실행함수
        """
        self.signal.login()


# 실행 스크립트
if __name__ == '__main__':
    """
    >> python3 1.Basic Structure.py 명령을 통해 실행하거나 IDE를 통해 직접 실행해볼 수 있다. 
    """

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = Bot()

    # 봇 작동시작
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()


"""
[실행결과]
코드를 작성하지 않아 별도의 실행결과 없음
"""