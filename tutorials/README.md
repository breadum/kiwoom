# Tutorials
Python wrapper of Kiwoom Open API+

## Library Structure

- 키움증권에서 제공하는 Open API+ 인터페이스의 간단한 Python Wrapper 모듈

- PyQt5를 이용해 직접 개발하고자 하는 사람을 위한 모듈로 부가적인 기능은 최대한 배제

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

