"""
로그인 후 유저 및 서버에 대한 정보 확인 예제 스크립트로 KOA Studio에서 아래 항목 참조

개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo
"""


import sys
from PyQt5.QtWidgets import QApplication
from kiwoom import Bot


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class MyBot(Bot):
    def __init__(self, server=None):
        """
        튜토리얼 2.Login.py 참고
        """
        # 상속받는 Bot 클래스 초기화 필수
        # self.api = Kiwoom() 설정됨
        super().__init__(server)

        # 사용할 변수 초기화
        self.acc = None

        # 이벤트 핸들러 연결
        self.api.connect(
            event='on_event_connect',
            signal=self.login,
            slot=self.server.login
        )

    def account(self):
        """
        기본적인 계좌 및 유저 정보 확인 요청함수

        * Note
        get_login_info 함수는 이벤트를 거치지 않고 즉시 요청값을 반환해주기 때문에,
        별도로 이벤트를 통해 요청한 데이터를 받아볼 수 있는 slot 함수와 api.loop()
        함수가 필요없다. 즉, Server 클래스의 사용이 필요없다.

        * KOA Studio 참고 가이드
        개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo
        """
        # 로그인 계좌 정보확인 API 개발가이드
        # help(Kiwoom.get_login_info)

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

    # 봇 작동시작
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
            raise RuntimeError(f"Server NOT Connected.")
            # or you may exit script - import sys; sys.exit()

        # 계좌 정보 출력
        info = self.account()
        print('-- 계좌 정보 --')
        for key, val in info.items():
            print(f'{key}: {val}')

        # ... to be continued


# 실행 스크립트
if __name__ == '__main__':
    """
    >> python3 4.Account.py 명령을 통해 실행하거나 IDE를 통해 직접 실행해볼 수 있다. 
    """

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = MyBot()

    # 로그인
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    #   - 메인 윈도우 창을 종료하면 스크립트 종료
    #   - app.exec() 단독 실행할 경우 작업관리자로 종료
    from PyQt5.QtWidgets import QMainWindow
    win = QMainWindow()
    win.setWindowTitle('Quit!')
    win.show()
    sys.exit(app.exec())


"""
[실행결과]

로그인 정상처리

* 시스템 점검
  - 월 ~ 토 : 05:05 ~ 05:10
  - 일 : 04:00 ~ 04:30

-- 계좌 정보 --
계좌개수: 2
계좌번호: ['xxxxxxxxxx', 'xxxxxxxxxx']
유저아이디: ------
유저이름: ㅇㅇㅇ
서버구분: 모의투자
"""
