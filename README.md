# Kiwoom Open API+
Python wrapper of Kiwoom Open API+

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
> on_receive_tr_condition(scr_no, code_list, condition_name, index, next)
> ```

#### 2. 통신을 위한 체계적인 코드 작성 지원

- 데이터를 요청하는 함수와 데이터를 받는 함수를 분리해서 작성 (Signal & Slot)

- 작성 후 Kiwoom.connect() 함수로 서로 연결시켜 서버에서 응답 시 자동 호출 지원

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
> ```
> ```python
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
> ```
> ```python
> # 구현되어있는 메인 클래스
> class Kiwoom:
>     ...
>     # rq_name = 'balance'라면, @Connector가 매핑된 함수를 자동 호출
>     # >> slot.balance(scr_no, rq_name, tr_code, record_name, prev_next)
>     @Connector(key='rq_name')
>     def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
>         pass
> ```

- 간단한 실행 스크립트 예시 (여러가지 방식 가능)

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
>     """
>     # Kiwoom.connect() 함수를 이용해 signal과 slot을 서로 매핑
>     # 자세한 내용은 >> help(Kiwoom.connect) 필히 참조
>     """
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

- loop / unloop 함수를 통해 간단히 코드 실행 / 대기 제어

> ```python
> from kiwoom import *
>
> # QEventLoop 활용
> api = Kiwoom()
> api.loop()
> api.unloop()
> ```

- 요청 후 처리 결과를 제공하는 함수에 한해 Exception 자동 발생

> ```python
> class Kiwoom:
>     ...
>     # 만일 send_order() 실행 후 정상처리 되지 않았다면 @catch_error 에서 Exception 자동 발생
>     # ex) An exception occured from send_order,  "-308 : OP_ERR_ORD_OVERFLOW (주문전송과부하)"
>     @catch_error
>     def send_order(self, rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no):
>         return super().send_order(rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no)
>     ...

- 시장과 섹터의 약속된 지정 번호와 이름 확인

> ```python
> import kiwoom
>
> # 단, 주기적 업데이트 필요!
> print(kiwoom.config.markets)  # {'0': 'KOSPI', '3': 'ELW', ... }
> print(kiwoom.config.sectors)  # {'001': '종합(KOSPI)', '002': '대형주', ... }
> ```

- 순수한 API 기능만을 사용하고 싶은 경우 지원

> ```python
> from kiwoom import API
>
> # Overriding
> class Bot(API):
>     pass
> ```

- API 이용 과정 로깅 기능 제공 (지원예정)

> ```python
> from kiwoom import *
> 
> api = Kiwoom()
> api.logging(True, path='log/20201015')
> api.logging(False)
> ```

- 주가, 지수, 섹터, 국내선옵 Historical Market Data 다운로드 (지원예정)

> ```python
> api.histories(market='KOSPI', period='tick', start='20201001', merge=True)
> api.histories(sector='금융업', period='tick', start='20201001', merge=True)
> ```

## Installation

#### Prerequisite

##### 1. 키움 Open API+ 사용 신청 (Step1), 모듈 다운로드 (Step2), KOA Studio 다운로드 (Step3)

- 키움 웹사이트 (https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)

##### 2. 32-bit Python 3.7 이상 Windows 환경 세팅

- 키움 Open API+ 활용 시 필수조건

- Anaconda 64-bit 에서 32-bit 가상환경 생성 시 유의사항

     네이버 블로그 참고 페이지 (https://m.blog.naver.com/haanoon/221814660104)

> ```bash
> # 실제로 잘 작동하지 않는 방식
> set CONDA_FORCE_32BIT=1  
>
> # 권장하는 방식 
> conda create -n your_awesome_bot  # 가상환경 생성
> conda activate your_awesome_bot  # 가상환경 실행
> conda config --env --set subdir win-32  # 현위치에서 32bit 설정
> conda install python=3.7  # Python 3.7 설치
> ```

- 아래 코드로 '32Bit'인지 반드시 확인 후 설치

> ```python
> import platform; print(platform.architecture())
> ```

##### 3. KOA Studio를 활용해 간단한 조회 후 데이터 수신 확인

- 키움에서 Open API+ 모듈을 받아도 처음 실행 시 여러가지 오류 발생

- 먼저 KOA Studio를 통해 오류 확인 및 해결 후 파이썬 모듈 설치

- 버전 업데이트, 계좌비밀번호 저장 및 AUTO 기능 등을 확인

#### Install from pip

> ```bash
> pip install kiwoom
> ```

#### Install from source

> ```bash
> # After git clone and cd into the dir
> python3 setup.py install
> ```

## License

- [MIT License][mit]

## Finally

- 본 프로젝트의 개발자는 키움증권과 아무런 관련이 없는 개인이 제작했습니다.

- 발생한 어떠한 손실에 대하여 어떻게 발생하였든지 개발자는 이에 대해 아무런 책임이 없음을 알립니다.

- 버그, 기능요청, 문의사항 등은 [Github 이슈 게시판][issue] 및 [E-mail][email]을 통해 남겨주세요.

[mit]: https://github.com/breadum/kiwoom/blob/main/LICENSE
[issue]: https://github.com/breadum/kiwoom/issues
[email]: https://github.com/breadum
