# Kiwoom Open API+
Python wrapper of Kiwoom Open API+ (키움증권)

## What is it?

키움증권에서 제공하는 Open API+ 인터페이스의 Python 버전   
PyQt5를 이용해 직접 개발하고자 하는 사람들을 위한 모듈

## Main Features

- Open API+ 함수 호출 간소화

  + 불필요한 dynamicCall 제거

Before

```python
self.dynamicCall("CommRqData(QString, QString, Int, QString)", rq_name, tr_code, prev_next, scr_no)
```

After

```python
self.comm_rq_data(rq_name, tr_code, prev_next, scr_no)
```

- Slot 함수를 

  + TR 예시

- loop/unloop 기능을 통해 간단한 제어

