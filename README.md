# Kiwoom Open API+
Python wrapper of Kiwoom Open API+ (키움증권)

## What is it?

- 키움증권에서 제공하는 Open API+ 인터페이스의 Simple Python Wrapper 모듈

- PyQt5를 이용해 직접 개발하고자 하는 분들을 위한 모듈로 부가적인 기능은 최대한 배제


## Main Features

#### Open API+ 함수 호출 간소화

> 반복되는 dynamicCall 제거
>      Before
>      ```python
>      self.dynamicCall("CommRqData(QString, QString, Int, QString)", rq_name, tr_code, prev_next, scr_no)
>      ```
	
	After

	```python
	self.comm_rq_data(rq_name, tr_code, prev_next, scr_no)
	```

- 서버에 데이터를 요청하는 함수(Signal)와 데이터를 받는 함수(Slot)를 분리해서 작성

  + TR 예시

- loop/unloop 기능을 통해 간단한 QEventLoop 제어

```python
self.loop()
self.unloop()
```

