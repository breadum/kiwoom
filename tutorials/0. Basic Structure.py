from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        self.api = api


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        self.api = api


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # Signal, Slot, Event 연결
        # self.api.connect()

    # 봇 작동시작
    def run(self):
        pass


# 실행 스크립트
if __name__ == '__main__':

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = Bot()

    # 봇 작동시작
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()
