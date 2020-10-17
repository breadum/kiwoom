from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


# 서버에 데이터를 요청하는 클래스
class Signal:
    def __init__(self, api):
        """
        :param api = Kiwoom() 여러 클래스에서 공통으로 사용할 Kiwoom 인스턴스
        """
        self.api = api

    def login(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect 참조
        comm_connect 실행 시 on_connect_event 함수가 호출된다.
        """
        # 서버에 접속 요청
        self.api.comm_connect()
        # [필수] 로그인 될 때까지 대기
        self.api.loop()

    def is_connected(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState 참조
        :return: 연결상태 확인 후 연결되어 있다면 True, 그렇지 않다면 False
        """
        # 0 (연결안됨), 1 (연결됨)
        state = self.api.get_connect_state()

        if state == 1:
            return True  # 연결된 경우
        return False  # 연결되지 않은 경우

    def account(self):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo 참조
        get_login_info 함수는 이벤트를 거치지 않고 즉시 요청값을 반환해준다.
        """
        # 로그인 계좌 정보확인 API 개발가이드
        # help(Kiwoom.get_login_info)

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


# 요청했던 데이터를 받는 클래스
class Slot:
    def __init__(self, api):
        """
        :param api = Kiwoom() 여러 클래스에서 공통으로 사용할 Kiwoom 인스턴스
        """
        self.api = api

    def login(self, err_code):
        """
        개발가이드 > 로그인 버전처리 > 관련함수 > OnEventConnect 참조
        comm_connect 실행 시 on_event_connect 함수가 호출될 때 이 함수가 호출되도록 한다.
        """
        # err_code와 그에 해당하는 메세지
        emsg = config.error.err_msg(err_code)
        # 로그인 성공/실패 출력
        print(f'로그인 {emsg}')
        # [필수] 대기중인 코드 실행
        self.api.unloop()


# Signal과 Slot을 활용하는 클래스
class Bot:
    def __init__(self):
        self.api = Kiwoom()
        self.signal = Signal(self.api)
        self.slot = Slot(self.api)

        # Signal 클래스에서 comm_connect 요청 후 서버 응답이 on_event_connect
        self.api.connect(slot=self.slot.login, event='on_event_connect')

    def run(self):
        # 로그인 요청
        self.signal.login()

        # 접속 성공여부 확인
        if self.api.get_connect_state() != 1:
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
