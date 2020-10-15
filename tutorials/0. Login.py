from PyQt5.QtWidgets import QApplication
from kiwoom import *

import sys


"""
로그인과 버전처리에 대한 예제 스크립트로 KOA Studio에서 아래 항목 참조

개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState
개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo
"""
if __name__ == '__main__':

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    api = Kiwoom()

    # 로그인
    api.login()

    # 로그인 실행 시 결과
    """
    로그인 0 : OP_ERR_NONE (정상처리)

    * 시스템 점검
    - 월 ~ 토: 05:05 ~ 05: 10
    - 일: 04:00 ~ 04: 30
    """

    # 접속 상태 확인
    help(api.get_connect_state)
    print('접속상태', api.get_connect_state())


    # 로그인 계좌 정보확인 API 가이드
    help(api.get_login_info)

    # 계좌 정보확인 API 활용 예시
    def account_info():
        # keys = ['ACCOUNT_CNT', 'ACCLIST', 'USER_ID', 'USER_NAME', 'GetServerGubun']

        cnt = int(api.get_login_info('ACCOUNT_CNT'))  # 계좌 개수
        accounts = api.get_login_info('ACCLIST').split(';')[:cnt]  # 계좌번호

        user_id = api.get_login_info('USER_ID')  # 유저 아이디
        user_name = api.get_login_info('USER_NAME')  # 유저 이름

        # 접속 서버 타입
        server = int(api.get_login_info('GetServerGubun'))
        server = '실서버' if server != 1 else '모의투자'

        # 정보 출력
        print(f'계좌 개수: {cnt}\n계좌 번호: {accounts}\n아이디: {user_id}\n이름: {user_name}\n서버: {server}')

    # 함수 실행
    account_info()

    # ---------- Optional Implementation (선택사항) ---------- #
    """
    만일 로그인 시 다르게 처리되고 싶다면 별도로 함수 지정
    api.login()을 호출해서 로그인 되었다면 api.on_event_connect(err_code) 함수가 자동 호출됨
    api.connect() 함수를 이용해 api.on_event_connect(err_code) 함수가 호출 될 때 다른 함수로 매핑할 수 있음
    """
    def login_slot(err_code):
        print('Login 성공')

    # 가능한 Event Handler 종류
    print(kiwoom.config.event_handlers)
    # on_event_connect에 대한 설명
    help(api.on_event_connect)
    # connect 함수에 대한 설명
    help(api.connect)

    # on_event_connect 함수가 호출될 때 login_slot이 불리도록 설정
    api.connect(slot=login_slot, event='on_event_connect')

    """
    # connect 후 로그인 시 결과 확인가능
    # 현재 스크립트는 이미 로그인이 되어있는 상태
    api.login()
    
    # 로그인 실행 결과
    # 'Login 성공'
    """
    # ------------------------------------------------------ #

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()
