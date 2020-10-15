# Kiwoom Open API+
Python wrapper of Kiwoom Open API+ (키움증권)

## What is it?

- 키움증권에서 제공하는 Open API+ 인터페이스의 간단한 Python Wrapper 모듈

- PyQt5를 이용해 직접 개발하고자 하는 분들을 위한 모듈로 부가적인 기능은 최대한 배제


## Main Features

#### 1. Open API+ 함수 호출 간소화

- 반복되는 dynamicCall 제거

> ```python
> # Before
> self.dynamicCall("CommRqData(QString, QString, Int, QString)", rq_name, tr_code, prev_next, scr_no)
> 
> # After
> self.comm_rq_data(rq_name, tr_code, prev_next, scr_no)
> ```

- 함수명과 변수명을 Python 방식으로 변경

> ```python
> # Before
> OnReceiveTrCondition(BSTR sScrNo, BSTR strCodeList, BSTR strConditionName, int nIndex, int nNext)
> 
> # After
> on_receive_tr_condition(scr_no, code_list, cond_name, index, next)
> ```

#### 2. 통신을 위한 체계적인 코드 작성 지원

- 데이터를 요청하는 함수와 데이터를 받는 함수를 분리해서 작성 (Signal & Slot)

- 작성 후 Kiwoom.connect() 함수로 매핑시켜 서버에서 응답 시 자동 호출 지원

> ```python
> # 서버에 데이터를 요청하는 클래스 (사용자 작성)
> class Signal: 
>     def __init__(self, api):
>         self.api = api
>     
>     def balance(self, prev_next='0'):
>         ...
>         # '계좌평가잔고내역'을 받기 위해 서버로 rq_name='balance'로 요청 전송
>         self.api.comm_rq_data(rq_name='balance', tr_code='opw00018', prev_next='0', scr_no='0000')
>         self.api.loop()  # 데이터를 다 받을 때까지 대기
>         ...
>
> # 서버에서 데이터를 받는 클래스 (사용자 작성)
> class Slot:
>     def __init__(self, api):
>         self.api = api
>         self.data = defaultdict(list)
>         self.is_downloading = False
>
>     def balance(self, scr_no, rq_name, tr_code, record_name, prev_next):
>         ...
>         # 만일 데이터가 더 있을 경우 연결했던 Signal 함수 다시 호출
>         if prev_next == '2':
>             fn = self.api.signal(rq_name)  # rq_name='balance'
>             fn(prev_next)  # signal.balance(prev_next='2')
>
>         # 데이터를 다 받았다면 unloop을 통해 대기중인 코드 실행
>         else:
>             ...
>             self.is_downloading = False
>             self.api.unloop()
>
> # 구현되어있는 메인 클래스
> class Kiwoom:
>     ...
>     # rq_name = 'balance'라면, @Connector가 매핑된 함수를 자동 호출
>     # >> slot.balance(scr_no, rq_name, tr_code, record_name, prev_next)
>     @Connector(key='rq_name')
>     def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
>         pass
> ```

- 간단한 실행 스크립트 예시

> ```python 
> from PyQt5.QtWidgets import QApplication
> from kiwoom import *
>
> import sys
>
> if __name__ == '__main__':
>     # 통신을 위해 QApplication 활용
>     app = QApplication(sys.argv)
>
>     # 인스턴스 생성
>     api = Kiwoom()
>     signal, slot = Signal(api), Slot(api)
>
>     # Kiwoom.connect() 함수를 이용해 signal과 slot을 서로 매핑
>     # 자세한 내용은 >> help(Kiwoom.connect) 참조
>     api.connect(signal.balance, slot.balance)
> 
>     # 버전처리 및 로그인 
>     api.login()
>
>     # 계좌평가잔고내역 요청
>     signal.balance()
>     
>     # 전송된 데이터 확인
>     print(slot.data)
>
>     # 데이터 수신을 위해 스크립트 종료 방지
>     app.exec()
> ```

#### 3. 디버깅을 위한 에러 출력

- PyQt5 모듈을 사용하는 경우 Pycharm과 같은 IDE 사용 시 에러 메세지가 발생하지 않는 문제 해결

#### 4. 간단한 기능 지원

- 로그인

> ```python
> from kiwoom import *
> api = Kiwoom()
> api.login()
> ```

- loop / unloop 함수를 통해 간단히 코드 실행 / 대기 제어 (QEventLoop)

> ```python
> from kiwoom import *
>
> api = Kiwoom()
> api.loop()
> api.unloop()
> ```

- 주가, 지수, 섹터, 국내선옵 Historical Market Data 다운로드 (지원예정)

> ```python
> api.history(market='KOSPI', period='tick', start='20201001', merge=True)
> ```

## Installation

#### Prerequisite

1. 키움 Open API+ 모듈 및 KOA Studio

     https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000

2. 32-bit Python 3.7 이상의 Windows 환경

> ```python
> import platform 
>
> print(platform.architecture())
> ```

#### From pip

> ```bash
> pip install kiwoom
> ```

#### From source

> ```bash
> # After git clone and cd into the dir
> python3 setup.py install
> ```
