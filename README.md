# Kiwoom Open API+
Python wrapper of Kiwoom Open API+ (키움증권)

## What is it?

키움증권에서 제공하는 Open API+ 인터페이스의 Python 버전

## Main Features

- 매번 입력해야하는 dynamicCall 제거

Before

	QAxWidget.dynamicCall("CommRqData(QString, QString, Int, QString)", rq_name, tr_code, prev_next, scr_no)

After


	api.comm_rq_data(rq_name, tr_code, prev_next, scr_no)

- asd

