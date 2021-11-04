"""
시장 데이터 수집을 위한 스크립트

1) 시장선택 
>> bot.histories(market='0', ...)  # KOSPI

config.MARKETS = {
    '0': 'KOSPI',
    '3': 'ELW',
    '4': '뮤추얼펀드',
    '5': '신주인수권',
    '6': '리츠',
    '8': 'ETF',
    '9': '하이일드펀드',
    '10': 'KOSDAQ',
    '30': 'K-OTC',
    '50': 'KONEX',
    '60': 'ETN'
}

2) 지수선택
>> bot.histories(sector='2', ...)  # KOSPI200

config.MARKET_GUBUNS = {
    '0': 'KOSPI',
    '1': 'KOSDAQ',
    '2': 'KOSPI200',
    '4': 'KOSPI100(150)',
    '7': 'KRX100'
}

# 각각의 시장구분 안에 아래 지수들이 적절히 포함되어 있다. 
# 시장구분이 '2'라면, KOSPI200의 지수들은 2로 시작한다.
# config.SECTORS = {
#     ...
#    '201': 'KOSPI200',
#    '207': 'F-KOSPI200',
#    '208': 'F-KOSPI200인버스',
#    '209': '레버리지KOSPI200',
#    '210': 'F-KOSPI200레버리지',
#    '211': '건설',
#    '212': '중공업',
#     ...
# }
"""


import sys
import time
from multiprocessing import Process, Manager

from PyQt5.QtWidgets import QApplication

from kiwoom import Bot, config
from kiwoom.config.types import ExitType
from kiwoom.utils import clock


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class MyBot(Bot):
    def run(self, kwargs=None):
        """
        Bot 실행함수

        1) 로그인
        2) 다운로드 시작
        3) 다운로드 결과 확인
        """
        # 경고 메세지 제거
        config.MUTE = True

        # 로그인 요청
        self.login()

        # 시장 데이터 요청
        kwargs = {
            # 1) 시장선택 - print(config.MARKETS), {'0': 'KOSPI', '10': 'KOSDAQ', ...}
            'market': '0',
            # 2) 기간선택 - print(config.PERIODS), ['tick', 'min', 'day', 'week', 'month', 'year']
            'period': 'tick',
            # 3) 저장위치 - 다운받은 데이터 csv 파일로 저장할 위치
            'path': 'C:/Data/market/KOSPI/tick',
            # 4) 병합 - 다운받은 데이터와 기존에 존재하는 csv 파일의 병합여부
            'merge': True,
            # 5) 경고 - 경고 메세지 출력 여부
            'warning': False
        } if kwargs is None else kwargs

        # 다운로드 시작
        result = self.histories(**kwargs)

        # 결과 확인
        # 1) 0 = ExitCode.SUCCESS : 완전히 다 받은 경우
        # 2) 1 = ExitCode.FAILURE : 다운 요청 중 오류가 난 경우
        # 3) slice = (from, to)   : 다운 완료 된 항목 제외 후 다시 시작할 위치
        print(f'다운로드 결과 = {result}')

        # 결과 반환
        return result


# 실행 스크립트
if __name__ == '__main__':
    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = MyBot()

    # 로그인 및 다운로드
    result = bot.run()

    # 다운로드 완료 시 종료
    app.exit(0)


"""
Multi-processing을 활용하여 24시간 다운로드 받을 수 있는 버전
"""


# 24시간 끊기지 않는 버전
def run_24(kwargs, share):
    # To make process stable
    time.sleep(5)

    # To suppress warning messages
    config.MUTE = True

    # 초기화 및 로그인
    app = QApplication(sys.argv)
    bot = MyBot()
    bot.login()

    """
    Hidden
    """

    # 다운로드 시작
    result = bot.histories(**kwargs)

    # 결과 저장 및 공유
    share['result'] = result
    share['complete'] = True

    # Bot 실행 종료
    app.exit()


# 24시간 끊기지 않는 버전 실행 스크립트
if __name__ == '__main__':
    # 프로그램 시작시 예/아니오 팝업을 없애기 위해 관리자 권한으로 실행
    from ctypes import windll
    if not windll.shell32.IsUserAnAdmin():
        raise EnvironmentError("Please run as root.")

    # Default args
    kwargs = {
        'market': '0',
        'period': 'tick',
        'start': '20210405',
        'end': '20210416',
        'merge': True,
        'warning': False,
        'path': 'C:/Data/market/KOSPI/tick'
    }

    # Variables to set
    ntry, maxtry = 0, 2

    # Share data between processes
    share = Manager().dict()
    share['complete'] = False
    share['impossible'] = False

    # Loop start
    while True:
        # Print time
        print(f"[{clock()}] Starting a new loop!")

        # Variables
        share['complete'] = False

        # Spawning a process
        p = Process(target=run_24, args=(kwargs, share), daemon=True)
        p.start()
        p.join()

        # 1) Download done
        if share['result'] == ExitType.SUCCESS:
            print(f"[{clock()}] Download done for {config.MARKETS[kwargs['market']]}!")
            time.sleep(1)
            break

        # 2) Download failed by local errors
        elif share['result'] == ExitType.FAILURE:
            # If maximum try, stop
            if ntry == maxtry:
                print(f'[{clock()}] Max tryout reached, stop downloading.')
                break
            # Else, try again
            ntry += 1
            time.sleep(1)
            print(f'[{clock()}] Retry downloading due to local errors.')

        # 3) Process killed due to no response from the server
        elif not share['complete']:
            print(f'[{clock()}] Take a 10 minute break for server to response.')
            time.sleep(10 * 60)

        # 4) Not allowed
        else:
            raise RuntimeError(f'[{clock()}] Download failed.')

    """
        # Hidden Case
        # 4) When script re-start is needed
        else:
            # In case, we have to slow down for the next run
            if share['result'] == ExitType.IMPOSSIBLE:
                share['impossible'] = True

            # Otherwise, speeding again
            else:
                # Update kwargs for restarting
                #  - Note that 'slice' and 'code' can't be used together
                kwargs['slice'] = share['result']
                if 'code' in kwargs:
                    del kwargs['code']
                
                # Update share
                share['impossible'] = False

                # Print result
                print(f"\n[{clock()}] Restart with slice={share['result']} in the next loop.")

        time.sleep(1)
    """

    # Script done
    print(f'[{clock()}] Script All Finished.')
