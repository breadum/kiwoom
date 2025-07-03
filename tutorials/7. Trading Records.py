"""
Trading Records(i.e. Transactions) 수신에 관한 스크립트

* 튜토리얼 중 '5. TR Data.py' 참고
* KOA Studio > TR 목록 > opw00007 참고
"""


import sys
import pandas as pd
    
from typing import Any
from pprint import pprint
from collections import defaultdict

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest

from kiwoom import Bot, Server
from kiwoom.utils import name


# 서버에 데이터를 요청하는 클래스 (사용자 작성)
class Bot(Bot):
    def __init__(self, server: Server | None = None):
        super().__init__(server)
        self.api.connect('on_event_connect', signal=self.login, slot=self.server.login)
        self.api.set_connect_hook('on_receive_tr_data', 'rq_name')
        self.api.connect('on_receive_tr_data', signal=self.record, slot=self.server.record)

    def account(self) -> dict[str, Any]:
        """
        튜토리얼 4.Account.py 참고
        """
        cnt: int = int(self.api.get_login_info('ACCOUNT_CNT'))  # 계좌개수
        accounts: list[str] = self.api.get_login_info('ACCLIST').split(';')[:cnt]  # 계좌번호

        # 접속 서버 타입
        server: str = self.api.get_login_info('GetServerGubun')
        server = '모의투자' if server.strip() == '1' else '실서버'
        
        # 계좌정보 반환
        return {  
            '계좌개수': cnt,
            '계좌번호': accounts,
            '서버구분': server
        }
    
    def record(self, date: str, acc: str, prev_next: str = '1') -> None:
        """
        튜토리얼 5. TR Data.py 참고
        """
        # 계좌별주문체결현황요청 TR
        tr_code: str = 'opw00009'

        # 서버 인스턴스와 컨텍스트 공유 및 데이터 초기화
        args: dict = {'date': date, 'acc': acc}
        self.share.update_args(name(), args)
        self.share.remove_multi(name())

        # 입력데이터
        inputs: dict[str, Any] = {
            '주문일자': date,  # YYYYMMDD
            '계좌번호': acc[:10],  # 10자리
            '비밀번호': '',
            '비밀번호입력매체구분': '00',
            '주식채권구분': 0,
            '시장구분': '0',
            '매도수구분': 0,
            '조회구분': 1,  # 체결
            '종목코드': '',
            '시작주문번호': '',
            '거래소구분': ''
        }
        for key, val in inputs.items():
            self.api.set_input_value(key, val)

        # 연속 조회 제한 회피를 위한 딜레이 3.6초
        QTest.qWait(3600) 

        # TR 요청 (계좌별주문체결현황요청)
        out: int = self.api.comm_rq_data('record', tr_code, prev_next, '0000')
        if out != 0:
            raise RuntimeError

        # on_receive_tr_data 이벤트 호출 대기
        self.api.loop()

    def records(self, ym: str, acc: str) -> dict[str, list]:
        """
        월별 거래내역 데이터 조회
        """
        # 주어진 월의 1일부터 말일까지 날짜 설정
        assert len(ym) == 6, "Argument 'ym' should be YYYYMM."
        start = pd.Timestamp(year=int(ym[:4]), month=int(ym[4:6]), day=1)
        end = start + pd.tseries.offsets.MonthEnd()
        end = min(pd.Timestamp.today(), end)
        
        # 평일 날짜별로 TR 요청
        data: dict[str: list] = defaultdict(list)
        for bday in pd.bdate_range(start, end):
            date = bday.strftime('%Y%m%d')
            self.record(date, acc, prev_next='0')
            if self.share.isin_multi('record'):
                rec: dict[str, list] = self.share.get_multi('record')
                for key, vals in rec.items():
                    data[key].extend(vals)
        
        # 데이터 반환
        return data


    def to_csv(self, file: str, data: dict[str, list]) -> None:
        """
        Excel로 보내기/저장 (키움증권 0343 화면)
        """
        if not data:
            print(f'No data to write. Skip writing.')
            return 
        
        # Pandas 활용한 전처리
        df = pd.DataFrame(data)
        
        ints = [
            '주문번호', '원주문번호', 
            '주문수량', '주문단가', 
            '확인수량', '스톱가', 
            '체결번호', '체결수량', '체결단가'
        ]
        for col in ints:
            df[col] = df[col].astype(int)
        
        df['주식채권'] = df['주식채권구분'].map({'1': '주식', '2': '채권'})
        df['원주문번호'] = df['원주문번호'].apply(lambda x: '' if x == 0 else str(x))
        df['종목번호'] = df['종목번호'].str[-6:]
        df['체결시간'] = df['체결시간'].str.lstrip('0')
        df.rename(
            columns={
                '체결단가': '체결평균단가',
                '정정취소구분': '정정/취소',
                '통신구분': '통신',
                '예약반대': '예약/반대',
                '거래소구분': '거래소'
            },
            inplace=True
        )

        # 키움증권 0343 화면 
        col1 = [  # 1st row 
            '주식채권', '주문번호', '원주문번호', '종목번호', '매매구분', 
            '주문유형구분', '주문수량', '주문단가', '확인수량', '체결번호', '스톱가'
        ]
        col2 = [  # 2nd row 
            '주문일자', '종목명', '접수구분', '신용거래구분', '체결수량', '체결평균단가', 
            '정정/취소', '통신', '예약/반대', '체결시간', '거래소'
        ]
        df = df.astype(str)
        with open(file, 'w', encoding='euc-kr') as f:
            # Header
            f.write(','.join(col1) + '\n')
            f.write(','.join(col2) + '\n')

            # Data
            lines = []
            row1 = df[col1]
            row2 = df[col2]
            for (_, r1), (_, r2) in zip(row1.iterrows(), row2.iterrows()):
                lines.append(','.join(r1) + '\n')
                lines.append(','.join(r2) + '\n')
            f.writelines(lines)

    def run(self):
        """
        작성했던 코드 실행함수
        """
        # 로그인 요청
        self.login()

        # 접속 성공여부 확인
        if not self.connected():
            raise RuntimeError(f"Server Not Connected.")

        # 계좌정보확인 요청
        info = self.account()
        pprint(info)

        # 거래내역 요청
        ym = '202507'
        acc = info['계좌번호'][0]
        data = self.records(ym, acc)

        # 데이터 엑셀 CSV 저장
        self.to_csv(f'{ym}.csv', data)
        

# 서버에서 데이터를 받아 처리하는 클래스 (사용자 작성)
class Server(Server):
    def __init__(self):
        super().__init__()
        self.downloading = False

    def record(self, scr_no, rq_name, tr_code, record_name, prev_next):
        # Bot 인스턴스에서 설정해둔 변수값 확인
        args = self.share.get_args(name())
        date = args['date']
        acc = args['acc'] 
        
        # 조회건수 확인
        n: str = self.api.get_comm_data(tr_code, rq_name, 0, '조회건수')
        if n == '':
            self.api.unloop()
            return
        
        # TR : opw00009 (키움증권 0343 화면)
        keys = [
            # 1st row 
            '주식채권구분', '주문번호', '원주문번호', '종목번호', '매매구분', 
            '주문유형구분', '주문수량', '주문단가', '확인수량', '체결번호', '스톱가',
            # 2nd row 
            '종목명', '접수구분', '신용거래구분', '체결수량', '체결단가', 
            '정정취소구분', '통신구분', '예약반대', '체결시간', '거래소구분'
        ]
        data = {key: list() for key in keys}
        cnt = self.api.get_repeat_cnt(tr_code, rq_name)
        for i in range(cnt):
            for key in keys:
                val = str(self.api.get_comm_data(tr_code, rq_name, i, key)).strip()
                data[key].append(val)
        
        # 데이터 저장
        for key in keys:
            self.share.extend_multi(name(), key, data[key])
        
        # 주문일자는 TR 'OUTPUT'에 없기 때문에 별도로 추가
        ymd = f'{date[:4]}-{date[4:6]}-{date[6:8]}'  # yyyy-mm-dd
        self.share.extend_multi(name(), '주문일자', [ymd] * cnt)

        # 데이터 연속조회
        if prev_next == '2':
            fn = self.api.signal('on_receive_tr_data', name())
            fn(date, acc, prev_next)
        
        # 데이터 조회완료
        else:
            self.downloading = False
            self.api.unloop()


# 실행 스크립트
if __name__ == '__main__':

    # 통신을 위해 QApplication 이용
    app = QApplication(sys.argv)

    # 인스턴스 생성
    bot = Bot(Server())

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
