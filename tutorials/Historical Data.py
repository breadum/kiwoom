from datetime import time

from kiwoom import *
from kiwoom.config.error import ExitCode

from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Manager

import sys

from kiwoom.utils import clock

"""

"""


class Bot(Bot):

    def run(self, kwargs=None):
        """
        작성했던 코드 실행함수

        1) 로그인
        2) 다운로드 시작
        3) 다운로드 결과 확인
        """
        # 로그인 요청
        self.login()

        # 시장 데이터 요청
        kwargs = {
            # 1) 시장선택 - print(config.markets), {'0': 'KOSPI', '10': 'KOSDAQ', ...}
            'market': '0',
            # 2) 기간선택 - print(config.periods), ['tick', 'min', 'day', 'week', 'month', 'year']
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
        # 1) 0 = ExitCode.success : 완전히 다 받은 경우
        # 2) 1 = ExitCode.failure : 다운 요청 중 오류가 난 경우
        # 3) slice = (from, None) : 서버 재부팅으로 연결 종료 후 재실행 시 시작할 위치 (다운 완료 된 항목 제외)
        print(f'다운로드 결과 = {result}')

        # 결과 반환
        return result


# 실행 스크립트
if __name__ == '__main__':
    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = Bot()

    # 로그인 및 다운로드
    result = bot.run()

    # 다운로드 완료 시 종료
    bot.exit(0)


"""
Multi-processing 활용하여 24시간 다운로드 받을 수 있는 버전 (고급과정)
"""


# 24시간 끊기지 않는 버전 (선택사항)
def run_24(kwargs, share):

    # 초기화 및 로그인
    app = QApplication(sys.argv)
    bot = Bot()
    bot.login()

    # 다운로드 시작
    result = bot.histories(**kwargs)

    # 다운로드가 완료된 경우
    if result == ExitCode.success:
        share['done'] = True
        share['error'] = False
        share['success'] = True

    # 다운로드 요청 중 오류 생긴 경우
    elif result == ExitCode.failure:
        share['done'] = False
        share['error'] = True
        share['success'] = False

    # 서버 재부팅으로 인한 종료시
    else:
        share['done'] = False
        share['error'] = False
        share['success'] = True
        share['slice'] = result

    # Bot 실행 종료
    bot.exit()


# 24시간 끊기지 않는 버전 실행 스크립트 (선택사항)
if __name__ == '__main__':

    # Default args
    kwargs = {
        'market': '0',
        'period': 'tick',
        'start': '20201215',
        'end': '20201230',
        'path': 'C:/Data/market/KOSPI/tick',
        'merge': True,
        'warning': False
    }

    # Variables to set
    ntry, maxtry = 0, 3
    share = Manager().dict()
    share['done'] = False
    share['error'] = False
    share['success'] = False

    # Loop start
    while True:
        # Print time
        print(f"Start new loop at {clock()}")

        # Variables
        share['error'] = False
        share['success'] = False

        # Spawning a process
        p = Process(target=run_24, args=(kwargs, share), daemon=True)
        p.start()
        p.join()

        # 1) Download done
        if share['done']:
            print(f'Download done at {clock()}')
            time.sleep(1)
            break

        # 2) Download failed by local error
        elif share['error']:
            # If tried three times, stop
            if ntry == maxtry:
                print(f'Stop downloading. Max tryout reached at {clock()}')
                break
            # Try again
            print(f'Retry downloading due to local error at {clock()}')
            ntry += 1
            time.sleep(1)
            continue

        # 3) Download failed due to no server response
        elif not share['success']:
            print(f'Take a 10 minutes break for server to reboot at {clock()}')
            time.sleep(10 * 60)
            continue

        # 4) Download success
        else:
            # Update kwargs
            #  - Note that 'slice' and 'code' can't be used together
            kwargs['slice'] = share['slice']
            if 'code' in kwargs:
                del kwargs['code']

            # Print result
            print(f"Time {clock()}, with \'slice\': {share['slice']}")
            time.sleep(1)

    # Script done
    if ntry == maxtry:
        print('Download Failure by some error.')
    print(f'Script Finished at {clock()}')

"""
기본적으로 on_receive_msg 이벤트가 처리되도록 구현되어 있어, 
중간에 계좌 조회 시 해당 이벤트로 인해 아래와 같은 메세지가 보일 수 있다. 

>> 화면번호: 0000, 요청이름: balance, TR코드: opw00018
>> [00Z310] 모의투자 조회가 완료되었습니다

메세지가 보이거나/보이지 않도록 하려면 다음 함수를 활용하면 된다.
>> Kiwoom.message(True)
>> Kiwoom.message(False)

[실행결과]
Login (Error - Code: 0, Type: OP_ERR_NONE, Msg: 정상처리)

Signal.deposit() 호출
	Slot.deposit(scr_no, rq_name, tr_code, record_name, prev_next, *args) 호출
	Slot.deposit(scr_no, rq_name, tr_code, record_name, prev_next, *args) 종료
Signal.deposit() 종료
Signal.balance(prev_next) 호출
	Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 호출
	Slot.balance(scr_no, rq_name, tr_code, record_name, prev_next, *args) 종료
Signal.balance(prev_next) 종료

-- 예수금확인 --
예수금 : 497,717,210원

-- 계좌잔고확인 --
Single Data: {
    '총평가손익금액': 1234567, 
    '총수익률(%)': 77.7
}
Multi Data: defaultdict(<class 'list'>,{
    '종목번호': ['A058820'], '종목명': ['CMG제약'], '평가손익': [1234567], 
    '수익률(%)': [77.7], '보유수량': [777], '매입가': [3333], '현재가': [7777]
})
"""