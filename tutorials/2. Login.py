"""
로그인과 버전처리에 대한 예제 스크립트 

* KOA Studio에서 아래 항목 참조
개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect
개발가이드 > 로그인 버전처리 > 관련함수 > GetConnectState
개발가이드 > 로그인 버전처리 > 관련함수 > GetLoginInfo

실제로 login 함수는 구현되어 있지만 튜토리얼을 위해 예시로 작성함.
"""


import sys
from PyQt5.QtWidgets import QApplication
from kiwoom import Bot, Server, config


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class MyBot(Bot):
    def __init__(self, server=None):
        # 상속받는 Bot 클래스 초기화 필수
        # self.api = Kiwoom() 설정됨
        super().__init__(server)

        """
        # Bot(Signal), Server(Slot) and Event 연결과정
        # 1) Bot 클래스에서 서버에 self.api.comm_connect() 함수를 통해 요청하면 
        # 2) 서버에서 응답이 오며 이벤트인 self.api.on_event_connect() 함수가 호출된다.
        # 3) 따라서 self.api.on_event_connect() 호출되면, self.server.login() 함수가 호출될 수 있도록 연결해 준다.
        
        # 자세한 사항은 KOA Studio 개발가이드와 help(Kiwoom.connect) 참조
        # 'on_event_connect' 이벤트의 경우 자동으로 signal, slot이 설정되어 있음
        """
        self.api.connect(
            event='on_event_connect',
            signal=self.login,
            slot=self.server.login
        )

    def login(self):
        """
        로그인 요청함수

        * Note
        comm_connect 실행 시 on_connect_event 함수가 호출된다.
        이 함수는 사실 이미 Bot 클래스에 간결하게 구현되어 있어서 다시 정의해 줄 필요는 없다.

        * KOA Studio 참고 가이드
        개발가이드 > 로그인 버전처리 > 관련함수 > CommConnect 참조
        """
        print('\tBot.login() 호출')

        # 연결 요청 API 가이드
        # help(Kiwoom.comm_connect)

        # 서버에 접속 요청
        self.api.comm_connect()

        # [필수] 이벤트가 호출될 때까지 대기 (on_event_connect)
        self.api.loop()

        print('\tBot.login() 종료')

    def connected(self):
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

    # 봇 작동시작
    def run(self):
        """
        작성했던 코드 실행함수

        1) 로그인
        2) 로그인 상태 확인
        """
        print('Bot.run() 호출')

        # 로그인 요청
        self.login()

        # 접속 성공여부 확인
        if not self.connected():
            raise RuntimeError(f'Server NOT connected.')
            # or you may exit script - import sys; sys.exit()

        # ... to be continued
        print('Bot.run() 종료')


# 서버에서 데이터를 받아 처리하는 클래스 (사용자 작성)
class MyServer(Server):
    def login(self, err_code):
        """
        Signal.login() 함수로 인해 OnEventConnect 이벤트 발생 시 로그인 메세지 처리함수

        * Note
        comm_connect 실행 결과로 on_event_connect 이벤트 함수가 호출될 때 이 함수가 호출되도록 한다.
        >> self.api.connect(event='on_event_connect', signal=self.login, slot=self.server.login)  # 31번째 줄 참고

        * KOA Studio 참고 가이드
        개발가이드 > 로그인 버전처리 > 관련함수 > OnEventConnect 참조
        """
        print('\t\tServer.login(err_code) 호출')

        # 접속 요청 시 발생하는 이벤트 API 가이드
        # help(Kiwoom.on_event_connect)

        # 에러 메세지 출력 함수 가이드
        # help(kiwoom.config.error.msg)

        # err_code에 해당하는 메세지
        emsg = config.error.msg(err_code)

        # 로그인 성공/실패 출력
        print(f'\t\tLogin ({emsg})')

        # [필수] 이벤트를 기다리며 대기중이었던 코드 실행 (60번째 줄)
        self.api.unloop()

        print('\t\tServer.login(err_code) 종료')


# 실행 스크립트
if __name__ == '__main__':
    """
    >> python3 2.Login.py 명령을 통해 실행하거나 IDE를 통해 직접 실행해볼 수 있다. 
    """

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = MyBot(MyServer())

    # 로그인
    bot.run()

    # 통신 유지를 위해 스크립트 종료 방지
    app.exec()


"""
[실행결과]

Bot.run() 호출
	Bot.login() 호출
		Server.login(err_code) 호출
		Login (정상처리)
		Server.login(err_code) 종료
	Bot.login() 종료
	현재 접속상태 = 1
Bot.run() 종료
"""
