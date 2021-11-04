"""
키움증권 Open API+ 활용을 위한 기본적인 Class 구성

1. API를 Python에서 활용할 수 있게 해주는 Kiwoom Class
2. 서버에 데이터를 요청하는 Bot Class (사용자 정의)
3. 서버에서 데이터를 받아 처리하는 Server Class (사용자 정의)

API와 사용자 정의 함수들을 연결해 활용할 수 있게 해주는 필수함수

1. Kiwoom.connect(event, signal, slot)
2. Kiwoom.set_connect_hook(event, arg)

구현에 도움을 주는 가이드

1. help(...) 내장함수
2. KOA Studio 개발가이드
3. 키움증권 Open API 고객문의 게시판
"""


import sys
from PyQt5.QtWidgets import QApplication
from kiwoom import Bot, Server


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class MyBot(Bot):
    def __init__(self, server=None):
        # 상속받는 Bot 클래스 초기화 필수
        # self.api = Kiwoom() 설정됨
        super().__init__(server)

        # Bot(Signal), Server(Slot) and Event 연결
        # 1) 로그인 요청 시 아래 이벤트가 호출된다. (KOA Studio 개발가이드 참조)
        event = 'on_event_connect'
        # 2) 해당 이벤트 호출 시 server.login() 함수가 자동호출 되도록 설정
        self.api.connect(event, signal=self.login, slot=self.server.login)

    # ex) 로그인을 요청하는 함수
    def login(self):
        pass

    # 봇 작동시작
    def run(self):
        """
        작성했던 코드 실행함수
        """
        self.login()


# 서버에서 데이터를 받아 처리하는 클래스 (사용자 작성)
class MyServer(Server):
    # ex) 서버로 부터 로그인 응답을 받았을 때 처리하는 함수
    def login(self):
        pass


# 실행 스크립트
if __name__ == '__main__':
    """
    >> python3 1.Basic Structure.py 명령을 통해 실행하거나 IDE를 통해 직접 실행해볼 수 있다. 
    """

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = MyBot(MyServer())

    # 봇 작동시작
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()


"""
[실행결과]
코드를 작성하지 않아 별도의 실행결과 없음
"""