from PyQt5.QAxContainer import QAxWidget


"""
Pure API module  
"""


class API(QAxWidget):
    """
    Python Wrapper Class of Kiwoom Open API+

    This class is just a pure python wrapper for the api. All methods should be found
    on KOA Studio manual. Implementation is based on PyQt5 to utilize Open API+. No
    additional method is defined in this class. Extra helpful method is defined at
    Kiwoom class which inherits this class to support implementors.
    """
    def __init__(self):
        # QAxWidget init
        super().__init__()

        # To shorten codes
        self.call = self.dynamicCall

        # To use Kiwoom OpenAPI+
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        # To connect event handler
        self.OnEventConnect.connect(self.on_event_connect)
        self.OnReceiveMsg.connect(self.on_receive_msg)
        self.OnReceiveTrData.connect(self.on_receive_tr_data)
        self.OnReceiveRealData.connect(self.on_receive_real_data)
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)
        self.OnReceiveConditionVer.connect(self.on_receive_condition_ver)
        self.OnReceiveTrCondition.connect(self.on_receive_tr_condition)
        self.OnReceiveRealCondition.connect(self.on_receive_real_condition)

    """
    로그인 버전처리
    """
    def comm_connect(self):
        """
        수동 로그인설정인 경우 로그인창을 출력해서 로그인을 시도하거나
        자동로그인 설정인 경우 로그인창 출력없이 로그인을 시도합니다.
        """
        return self.call("CommConnect()")
        
    def get_connect_state(self):
        """
        현재 로그인 상태를 알려줍니다.
        리턴값 1:연결, 0:연결안됨
        """
        return self.call("GetConnectState()")
        
    def get_login_info(self, tag):
        """
        'ACCOUNT_CNT' : 보유계좌 수를 반환합니다.
        'ACCLIST' 또는 "ACCNO" : 구분자 ';'로 연결된 보유계좌 목록을 반환합니다.
        'USER_ID' : 사용자 ID를 반환합니다.
        'USER_NAME' : 사용자 이름을 반환합니다.
        'KEY_BSECGB' : 키보드 보안 해지여부를 반환합니다.(0 : 정상, 1 : 해지)
        'FIREW_SECGB' : 방화벽 설정여부를 반환합니다.(0 : 미설정, 1 : 설정, 2 : 해지)
        'GetServerGubun' : 접속서버 구분을 반환합니다.(1 : 모의투자, 나머지 : 실서버)
        """
        return self.call("GetLoginInfo(QString)", tag)

    """
    조회와 실시간데이터처리
    """
    def comm_rq_data(self, rq_name, tr_code, prev_next, scr_no):
        """
        CommRqData(
            BSTR sRQName,    // 사용자 구분명
            BSTR sTrCode,    // 조회하려는 TR이름
            long nPrevNext,  // 연속조회여부
            BSTR sScreenNo  // 화면번호
        )
          
        조회요청함수이며 빈번하게 조회요청하면 시세과부하 에러값으로 -200이 전달됩니다.
        > 리턴값
           0 : 조회요청정상 (나머지는 에러)
        -200 : 시세과부하
        -201 : 조회전문작성 에러
        """
        return self.call("CommRqData(QString, QString, Int, QString)", rq_name, tr_code, prev_next, scr_no)

    def set_input_value(self, id, value):
        """
        SetInputValue(
            BSTR sID,     // TR에 명시된 Input이름
            BSTR sValue   // Input이름으로 지정한 값
        )
          
        조회요청시 TR의 Input값을 지정하는 함수이며 조회 TR 입력값이 많은 경우 이 함수를 반복적으로 호출합니다.

        -------------------------------------------------------------------------------------------------------

        [OPT10081 : 주식일봉차트조회요청예시]

        SetInputValue("종목코드",  "039490"); // 첫번째 입력값 설정
        SetInputValue("기준일자",  "20160101");// 두번째 입력값 설정
        SetInputValue("수정주가구분",  "1"); // 세번째 입력값 설정
        LONG lRet = CommRqData( "RQName","OPT10081", "0","0600");// 조회요청
          
        -------------------------------------------------------------------------------------------------------
        """
        self.call("SetInputValue(QString, QString)", id, value)

    def disconnect_real_data(self, scr_no):
        """
        DisconnectRealData(
          BSTR sScnNo // 화면번호
        )
          
        화면번호 설정한 실시간 데이터를 해지합니다.
        """
        self.call("DisconnectRealData(QString)", scr_no)
    
    def get_repeat_cnt(self, tr_code, rq_name):
        """
        GetRepeatCnt(
            BSTR sTrCode, // TR 이름
            BSTR sRecordName // 레코드 이름
        )

        조회수신한 멀티데이터의 갯수(반복)수를 얻을수 있습니다. 예를들어 차트조회는 한번에 최대 900개
        데이터를 수신할 수 있는데 이렇게 수신한 데이터갯수를 얻을때 사용합니다.
        이 함수는 반드시 OnReceiveTRData()이벤트가 호출될때 그 안에서 사용해야 합니다.

        -------------------------------------------------------------------------------------------------------

        [OPT10081 : 주식일봉차트조회요청예시]

        OnReceiveTrDataKhopenapictrl(...)
        {
          if(strRQName == _T("주식일봉차트"))
          {
            int nCnt = OpenAPI.GetRepeatCnt(sTrcode, strRQName);
            for (int nIdx = 0; nIdx < nCnt; nIdx++)
            {
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("종목코드"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("거래량"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("시가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("고가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("저가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("현재가"));   strData.Trim();
            }
          }
        }
          
        -------------------------------------------------------------------------------------------------------
        """
        return self.call("GetRepeatCnt(QString, QString)", tr_code, rq_name)

    def comm_kw_rq_data(self, arr_code, next, code_cnt, type_flag, rq_name, scr_no):
        """
        CommKwRqData(
            BSTR sArrCode,    // 조회하려는 종목코드 리스트
            BOOL bNext,   // 연속조회 여부 0:기본값, 1:연속조회(지원안함)
            int nCodeCount,   // 종목코드 갯수
            int nTypeFlag,    // 0:주식 관심종목, 3:선물옵션 관심종목
            BSTR sRQName,   // 사용자 구분명
            BSTR sScreenNo    // 화면번호
        )

        한번에 100종목을 조회할 수 있는 관심종목 조회함수인데 영웅문HTS [0130] 관심종목 화면과는
        이름만 같은뿐 전혀관련이 없습니다. 함수인자로 사용하는 종목코드 리스트는 조회하려는\
        종목코드 사이에 구분자';'를 추가해서 만들면 됩니다.

        조회데이터는 관심종목정보요청(OPTKWFID) Output을 참고하시면 됩니다.
        이 TR은 CommKwRqData()함수 전용으로 임의로 사용하시면 에러가 발생합니다.
        """
        fn = "CommKwRqData(QString, Bool, Int, Int, QString, QString)"
        args = (arr_code, next, code_cnt, type_flag, rq_name, scr_no)
        return self.call(fn, args)
    
    def get_comm_data(self, tr_code, rq_name, index, item_name):
        """
        GetCommData(
            BSTR strTrCode,   // TR 이름
            BSTR strRecordName,   // 레코드이름
            long nIndex,      // TR반복부
            BSTR strItemName) // TR에서 얻어오려는 출력항목이름
        )

        OnReceiveTRData()이벤트가 호출될때 조회데이터를 얻어오는 함수입니다.
        이 함수는 반드시 OnReceiveTRData()이벤트가 호출될때 그 안에서 사용해야 합니다.

        -----------------------------------------------------------------------------------------------------

        [OPT10081 : 주식일봉차트조회요청예시]

        OnReceiveTrDataKhopenapictrl(...)
        {
          if(strRQName == _T("주식일봉차트"))
          {
            int nCnt = OpenAPI.GetRepeatCnt(sTrcode, strRQName);
            for (int nIdx = 0; nIdx < nCnt; nIdx++)
            {
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("종목코드"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("거래량"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("시가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("고가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("저가"));   strData.Trim();
              strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("현재가"));   strData.Trim();
            }
          }
        }

        -----------------------------------------------------------------------------------------------------
        """
        return self.call("GetCommData(QString, QString, Int, QString)", tr_code, rq_name, index, item_name)
    
    def get_comm_real_data(self, tr_code, fid):
        """
        GetCommRealData(
          BSTR strCode,   // 종목코드
          long nFid   // 실시간 타입에 포함된FID
        )

        OnReceiveRealData()이벤트가 호출될때 실시간데이터를 얻어오는 함수입니다.
        이 함수는 반드시 OnReceiveRealData()이벤트가 호출될때 그 안에서 사용해야 합니다.

        ------------------------------------------------------------------------------------------------------

        [주식체결 실시간 데이터 예시]

        if(strRealType == _T("주식체결"))
        {
          strRealData = m_KOA.GetCommRealData(strCode, 10);   // 현재가
          strRealData = m_KOA.GetCommRealData(strCode, 13);   // 누적거래량
          strRealData = m_KOA.GetCommRealData(strCode, 228);    // 체결강도
          strRealData = m_KOA.GetCommRealData(strCode, 20);  // 체결시간
        }

        ------------------------------------------------------------------------------------------------------
        """
        return self.call("GetCommRealData(QString, Int)", tr_code, fid)
    
    def get_comm_data_ex(self, tr_code, rq_name):
        """
        GetCommDataEx(
          BSTR strTrCode,   // TR 이름
          BSTR strRecordName  // 레코드이름
        )

        조회 수신데이터 크기가 큰 차트데이터를 한번에 가져올 목적으로 만든 전용함수입니다.

        ------------------------------------------------------------------------------------------------------

        [차트일봉데이터 예시]

        OnReceiveTrDataKhopenapictrl(...)
        {
          if(strRQName == _T("주식일봉차트"))
          {
              VARIANT   vTemp = OpenAPI.GetCommDataEx(strTrCode, strRQName);
              long	lURows, lUCols;
              long	nIndex[2]
              COleSafeArray saMatrix(vTemp);
              VARIANT vDummy;
              VariantInit(&vDummy);
              saMatrix.GetUBound(1, &lURows); // 데이터 전체갯수(데이터 반복횟수)
              saMatrix.GetUBound(2, &lUCols); // 출력항목갯수

              for(int nRow = 0; nRow <= lURows; nRow ++)
              {
                for(int nCol = 0; nCol <= lUCols; nCol ++)
                {
                  nIndex[0] = lURows;
                  nIndex[1] = lUCols;
                  saMatrix.GetElement(nIndex, &vDummy);
                  ::SysFreeString(vDummy.bstrVal);
                }
              }
            saMatrix.Clear();
            VariantClear(&vTemp);
          }
        }

        ------------------------------------------------------------------------------------------------------
        """
        return self.call("GetCommDataEx(QString, QString)", tr_code, rq_name)

    """
    주문과 잔고처리
    """
    def send_order(self, rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no):
        """
        SendOrder(
          BSTR sRQName, // 사용자 구분명
          BSTR sScreenNo, // 화면번호
          BSTR sAccNo,  // 계좌번호 10자리
          LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
          BSTR sCode, // 종목코드
          LONG nQty,  // 주문수량
          LONG nPrice, // 주문가격
          BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
          BSTR sOrgOrderNo  // 원주문번호입니다. 신규주문에는 공백, 정정(취소)주문할 원주문번호를 입력합니다.
        )

        9개 인자값을 가진 국내 주식주문 함수이며 리턴값이 0이면 성공이며 나머지는 에러입니다.
        1초에 5회만 주문가능하며 그 이상 주문요청하면 에러 -308을 리턴합니다.

        [거래구분]
        모의투자에서는 지정가 주문과 시장가 주문만 가능합니다.

        00 : 지정가
        03 : 시장가
        05 : 조건부지정가
        06 : 최유리지정가
        07 : 최우선지정가
        10 : 지정가IOC
        13 : 시장가IOC
        16 : 최유리IOC
        20 : 지정가FOK
        23 : 시장가FOK
        26 : 최유리FOK
        61 : 장전시간외종가
        62 : 시간외단일가매매
        81 : 장후시간외종가
        """
        fn = "SendOrder(QString, QString, QString, Int, QString, Int, Int, QString, QString)"
        args = (rq_name, scr_no, acc_no, ord_type, code, qty, price, hoga_gb, org_order_no)
        return self.call(fn, args)
        
    def send_order_fo(self, rq_name, scr_no, acc_no, code, ord_kind, sl_by_tp, ord_tp, qty, price, org_ord_no):
        """
        SendOrderFO(
          BSTR sRQName,     // 사용자 구분명
          BSTR sScreenNo,   // 화면번호
          BSTR sAccNo,      // 계좌번호 10자리
          BSTR sCode,       // 종목코드
          LONG lOrdKind,    // 주문종류 1:신규매매, 2:정정, 3:취소
          BSTR sSlbyTp,     // 매매구분	1: 매도, 2:매수
          BSTR sOrdTp,      // 거래구분(혹은 호가구분)은 아래 참고
          LONG lQty,        // 주문수량
          BSTR sPrice,      // 주문가격
          BSTR sOrgOrdNo    // 원주문번호
        )

        코스피지수200 선물옵션, 주식선물 전용 주문함수입니다.

        [거래구분]
        1 : 지정가
        2 : 조건부지정가
        3 : 시장가
        4 : 최유리지정가
        5 : 지정가(IOC)
        6 : 지정가(FOK)
        7 : 시장가(IOC)
        8 : 시장가(FOK)
        9 : 최유리지정가(IOC)
        A : 최유리지정가(FOK)
        """
        fn = "SendOrder(QString, QString, QString, Int, QString, Int, Int, QString, QString)"
        args = (rq_name, scr_no, acc_no, code, ord_kind, sl_by_tp, ord_tp, qty, price, org_ord_no)
        return self.call(fn, args)

    def send_order_credit(self, rq_name, scr_no, acc_no, order_type, code, qty, 
                          price, hoga_gb, credit_gb, loan_date, org_order_no):
        """
        SendOrderCredit(
          BSTR sRQName,   // 사용자 구분명
          BSTR sScreenNo,   // 화면번호 
          BSTR sAccNo,    // 계좌번호 10자리 
          LONG nOrderType,    // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
          BSTR sCode,   // 종목코드
          LONG nQty,    // 주문수량
          LONG nPrice,    // 주문가격
          BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
          BSTR sCreditGb, // 신용거래구분
          BSTR sLoanDate,   // 대출일
          BSTR sOrgOrderNo    // 원주문번호
        )
          
        국내주식 신용주문 전용함수입니다. 대주거래는 지원하지 않습니다.

        [거래구분]
        모의투자에서는 지정가 주문과 시장가 주문만 가능합니다.
          
        00 : 지정가
        03 : 시장가
        05 : 조건부지정가
        06 : 최유리지정가
        07 : 최우선지정가
        10 : 지정가IOC
        13 : 시장가IOC
        16 : 최유리IOC
        20 : 지정가FOK
        23 : 시장가FOK
        26 : 최유리FOK
        61 : 장전시간외종가
        62 : 시간외단일가매매
        81 : 장후시간외종가

        [신용거래]
        신용거래 구분은 다음과 같습니다.
        03 : 신용매수 - 자기융자
        33 : 신용매도 - 자기융자
        99 : 신용매도 자기융자 합

        대출일은 YYYYMMDD형식이며 신용매도 - 자기융자 일때는 종목별 대출일을 입력하고 신용매도 - 융자합이면 "99991231"을 입력합니다.
        """
        fn = "SendOrderCredit(QString, QString, QString, Int, QString, Int, Int, QString, QString, QString, QString)"
        args = (rq_name, scr_no, acc_no, order_type, code, qty, price, hoga_gb, credit_gb, loan_date, org_order_no)
        return self.call(fn, args)
        
    def get_chejan_data(self, fid):
        """
        [GetChejanData() 함수]

        GetChejanData(
          long nFid   // 실시간 타입에 포함된FID
        )

        OnReceiveChejan()이벤트가 호출될때 체결정보나 잔고정보를 얻어오는 함수입니다.
        이 함수는 반드시 OnReceiveChejan()이벤트가 호출될때 그 안에서 사용해야 합니다.
        """
        return self.call("GetChejanData(Int)", fid)

    """
    조건검색
    """
    def get_condition_load(self):
        """
        [GetConditionLoad() 함수]

        사용자 조건검색 목록을 서버에 요청합니다. 조건검색 목록을 모두 수신하면 OnReceiveConditionVer()이벤트가 호출됩니다.
        조건검색 목록 요청을 성공하면 1, 아니면 0을 리턴합니다.
        """
        return self.call("GetConditionLoad()")

    def get_condition_name_list(self):
        """
        [GetConditionNameList() 함수]

        서버에서 수신한 사용자 조건식을 조건명 인덱스와 조건식 이름을 한 쌍으로 하는 문자열들로 전달합니다.
        조건식 하나는 조건명 인덱스와 조건식 이름은 '^'로 나뉘어져 있으며 각 조건식은 ';'로 나뉘어져 있습니다.
        이 함수는 반드시 OnReceiveConditionVer()이벤트에서 사용해야 합니다.
        """
        return self.call("GetConditionNameList()")
    
    def send_condition(self, scr_no, cond_name, index, search):
        """
        [SendCondition() 함수]

        SendCondition(
          BSTR strScrNo,    // 화면번호
          BSTR strConditionName,  // 조건식 이름
          int nIndex,     // 조건명 인덱스
          int nSearch   // 조회구분, 0:조건검색, 1:실시간 조건검색
        )

        서버에 조건검색을 요청하는 함수로 맨 마지막 인자값으로 조건검색만 할것인지 실시간 조건검색도 할 것인지를 지정할 수 있습니다.
        여기서 조건식 인덱스는 GetConditionNameList()함수가 조건식 이름과 함께 전달한 조건명 인덱스를 그대로 사용해야 합니다.
        리턴값 1이면 성공이며, 0이면 실패입니다.
        요청한 조건식이 없거나 조건명 인덱스와 조건식이 서로 안맞거나 조회횟수를 초과하는 경우 실패하게 됩니다.

        ------------------------------------------------------------------------------------------------------

        [조건검색 사용예시]
        GetConditionNameList()함수로 얻은 조건식 목록이 "0^조건식1;3^조건식1;8^조건식3;23^조건식5"일때 조건식3을 검색

        long lRet = SendCondition("0156", "조건식3", 8, 1);

        ------------------------------------------------------------------------------------------------------
        """
        if self.call("SendCondition(QString, QString, Int, Int)", scr_no, cond_name, index, search) == 0:
            raise Exception(f'SendCondition() failed.\n{help(self.send_condition)}')
    
    def send_condition_stop(self, scr_no, cond_name, index):
        """
        [SendConditionStop() 함수]

        SendConditionStop(
          BSTR strScrNo,    // 화면번호
          BSTR strConditionName,    // 조건식 이름
          int nIndex    // 조건명 인덱스
        )

        조건검색을 중지할 때 사용하는 함수입니다.
        조건식 조회할때 얻는 조건식 이름과 조건명 인덱스 쌍을 맞춰서 사용해야 합니다.
        """
        self.call("SendConditionStop(QString, QString, Int)", scr_no, cond_name, index)

    def set_real_reg(self, scr_no, code_list, fid_list, opt_type):
        """
        [SetRealReg() 함수]

        SetRealReg(
          BSTR strScreenNo,   // 화면번호
          BSTR strCodeList,   // 종목코드 리스트
          BSTR strFidList,  // 실시간 FID리스트
          BSTR strOptType   // 실시간 등록 타입, 0또는 1
        )

        실시간 시세를 받으려는 종목코드와 FID 리스트를 이용해서 실시간 시세를 등록하는 함수입니다.
        한번에 등록가능한 종목과 FID갯수는 100종목, 100개 입니다.
        실시간 등록타입을 0으로 설정하면 등록한 종목들은 실시간 해지되고 등록한 종목만 실시간 시세가 등록됩니다.
        실시간 등록타입을 1로 설정하면 먼저 등록한 종목들과 함께 실시간 시세가 등록됩니다

        ------------------------------------------------------------------------------------------------------

        [실시간 시세등록 예시]
        OpenAPI.SetRealReg(_T("0150"), _T("039490"), _T("9001;302;10;11;25;12;13"), "0");  // 039490종목만 실시간 등록
        OpenAPI.SetRealReg(_T("0150"), _T("000660"), _T("9001;302;10;11;25;12;13"), "1");  // 000660 종목을 실시간 추가등록

        ------------------------------------------------------------------------------------------------------
        """
        return self.call("SetRealReg(QString, QString, QString, QString)", scr_no, code_list, fid_list, opt_type)

    def set_real_remove(self, scr_no, del_code):
        """
        [SetRealRemove() 함수]

        SetRealRemove(
          BSTR strScrNo,    // 화면번호 또는 ALL
          BSTR strDelCode   // 종목코드 또는 ALL
        )

        실시간 시세해지 함수이며 화면번호와 종목코드를 이용해서 상세하게 설정할 수 있습니다.

        ------------------------------------------------------------------------------------------------------

        [실시간 시세해지 예시]
        OpenAPI.SetRealRemove("0150", "039490");  // "0150"화면에서 "039490"종목해지
        OpenAPI.SetRealRemove("ALL", "ALL");  // 모든 화면에서 실시간 해지
        OpenAPI.SetRealRemove("0150", "ALL");  // 모든 화면에서 실시간 해지
        OpenAPI.SetRealRemove("ALL", "039490");  // 모든 화면에서 실시간 해지
          
          ------------------------------------------------------------------------------------------------------
        """
        self.call("SetRealRemove(QString, QString)", scr_no, del_code)

    """
    기타함수
    """
    def get_code_list_by_market(self, market):
        """
        [GetCodeListByMarket() 함수]

        GetCodeListByMarket(
          BSTR sMarket    // 시장구분값
        )

        국내 주식 시장별 종목코드를 ';'로 구분해서 전달합니다. 만일 시장구분값이 NULL이면 전체 시장코드를 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.

        [시장구분값]
        0 : 장내
        10 : 코스닥
        3 : ELW
        8 : ETF
        50 : KONEX
        4 :  뮤추얼펀드
        5 : 신주인수권
        6 : 리츠
        9 : 하이얼펀드
        30 : K-OTC
        """
        return self.call("GetCodeListByMarket(QString)", market)
    
    def get_master_code_name(self, code):
        """
        [GetMasterCodeName() 함수]

        GetMasterCodeName(
          BSTR strCode    // 종목코드
        )

        종목코드에 해당하는 종목명을 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterCodeName(QString)", code)
    
    def get_master_listed_stock_cnt(self, code):
        """
        [GetMasterListedStockCnt() 함수]

        GetMasterListedStockCnt(
          BSTR strCode  // 종목코드
        )

        입력한 종목코드에 해당하는 종목 상장주식수를 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterListedStockCnt(QString)", code)
    
    def get_master_construction(self, code):
        """
        [GetMasterConstruction() 함수]

        GetMasterConstruction(
          BSTR strCode  // 종목코드
        }

        입력한 종목코드에 해당하는 종목의 감리구분(정상, 투자주의, 투자경고, 투자위험, 투자주의환기종목)을 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterConstruction(QString)", code)
    
    def get_master_listed_stock_date(self, code):
        """
        [GetMasterListedStockDate() 함수]

        GetMasterListedStockDate(
          BSTR strCode    // 종목코드
        )

        입력한 종목의 상장일을 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterListedStockDate(QString)", code)
    
    def get_master_last_price(self, code):
        """  
        [GetMasterLastPrice() 함수]

        GetMasterLastPrice(
          BSTR strCode    // 종목코드
        )

        입력한 종목의 전일가를 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterLastPrice(QString)", code)
    
    def get_master_stock_state(self, code):
        """  
        [GetMasterStockState() 함수]

        GetMasterStockState(
          BSTR strCode  // 종목코드
        )

        입력한 종목의 증거금 비율, 거래정지, 관리종목, 감리종목, 투자융의종목, 담보대출, 액면분할, 신용가능 여부를 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetMasterStockState(QString)", code)
    
    def get_branch_code_name(self):
        """  
        [GetBranchCodeName() 함수]

        TR 조회에 필요한 회원사 정보를 회원사 코드와 회원사 이름으로 구성해서 전달합니다.
        각 회원사 정보는 구분자 ';'로 분리되어 있으며 한 회원사 정보에는 구분자 '|'로 회원사 코드와 회원사 이름을 분리합니다.
        전체적인 회원사 구성과 함수에서 전달받은 회원사 정보는 다음과 같습니다.

        "회원사코드0|회원사이름0;회원사코드1|회원사이름1;...회원사코드n|회원사이름n;"
        예) 001|교  보;002|신한금융투자;003|한국투자증권;...;827|모아증권중개;829|동양오리온

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetBranchCodeName()")
    
    def get_future_list(self):
        """  
        [GetFutureList() 함수]

        지수선물 종목코드 리스트를 ';'로 구분해서 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetFutureList()")
    
    def get_act_price_list(self):
        """  
        [GetActPriceList() 함수]

        지수옵션 행사가에 100을 곱해서 소수점이 없는 값을 ';'로 구분해서 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.

        ------------------------------------------------------------------------------------------------------

        [지수옵션 행사가 사용예시]
        CString strActPriceList(OpenAPI.GetActPriceList());
        "19000;19250;19500;19750;20000;20250;20500;20750;21000;21250;21500;21750;..."

        ------------------------------------------------------------------------------------------------------

        """
        return self.call("GetActPriceList()")
    
    def get_month_list(self):
        """  
        [GetMonthList() 함수]

        지수옵션 월물정보를 ';'로 구분해서 전달하는데 순서는 콜 11월물 ~ 콜 최근월물 풋 최근월물 ~ 풋 최근월물가 됩니다.

        로그인 한 후에 사용할 수 있는 함수입니다.

        ------------------------------------------------------------------------------------------------------

        [지수옵션 월물조회 사용예시]
        CString strMonthList(OpenAPI.GetMonthList());
        "201812;201806;201712;201706;201703;201612;201611;201610;201609;201608;201607;..."

        ------------------------------------------------------------------------------------------------------

        """
        return self.call("GetMonthList()")
    
    def get_option_code(self, act_price, cp, month):
        """
        [GetOptionCode() 함수]

        GetOptionCode(
          BSTR strActPrice,   // 소수점을 포함한 행사가
          int nCp,    // 콜풋구분값, 콜:2, 풋:3
          BSTR strMonth   // 6자리 월물
        )

        인자로 지정한 지수옵션 코드를 전달합니다.

        로그인 한 후에 사용할 수 있는 함수입니다.

        ------------------------------------------------------------------------------------------------------

        [지수옵션 코드 사용예시]

        CString strOptCode = OpenAPI.GetOptionCode(_T("247.50"), 2, _T("201607"));

        ------------------------------------------------------------------------------------------------------

        """
        return self.call("GetOptionCode(QString, Int, QString)", act_price, cp, month)
    
    def get_option_atm(self):
        """  
        [GetOptionATM() 함수]

        지수옵션 소수점을 제거한 ATM값을 전달합니다. 예를들어 ATM값이 247.50 인 경우 24750이 전달됩니다.

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetOptionATM()")
    
    def get_futures_list(self, base_asset_gb=""):
        """
        [GetSFutureList() 함수]

        GetSFutureList(
          BSTR strBaseAssetGb,   // 기초자산 구분값
        )

        기초자산 구분값을 인자로 받아서 주식선물 종목코드, 종목명, 기초자산이름을 구할수 있습니다.
        주식선물 전체 종목코드를 얻으려면 인자값이 공백처리 하면 됩니다.
        전달되는 데이터 형식은 다음과 같습니다.
        "종목코드1^종목명1^기초자산이름1;종목코드2^종목명2^기초자산이름2;...;종목코드n^종목명n^기초자산이름n;"

        로그인 한 후에 사용할 수 있는 함수입니다.
        """
        return self.call("GetSFutureList(QString)", base_asset_gb)

    def koa_functions(self, function_name, arg=''):
        """
        [KOA_Functions() 함수]

        KOA_Functions(
          BSTR sFunctionName,   // 함수이름 혹은 기능이름
          BSTR sParam   // 함수 매개변수
        )

        KOA_Function() 함수는 OpenAPI기본 기능외에 기능을 사용하기 쉽도록 만든 함수이며 두 개 인자값을 사용합니다.
        이 함수가 제공하는 기능과 필요한 인자값은 공지를 통해 제공할 예정입니다.

        ------------------------------------------------------------------------------------------------------

        [KOA_Functions() 함수 사용예시]

        1. 계좌비밀번호 설정창표시
        OpenAPI.KOA_Functions(_T("ShowAccountWindow"), _T(""));// 계좌비밀번호 설정창을 출력한다.

        2. 접속서버확인
        OpenAPI.KOA_Functions(_T("GetServerGubun"), _T(""));// 접속서버 구분을 알려준다. 1:모의투자 접속, 나머지:실서버 접속

        3. 주식종목 시장구분, 종목분류등 정보제공
        OpenAPI.KOA_Functions(_T("GetMasterStockInfo"), _T("039490"));
        호출결과는 입력한 종목에 대한 대분류, 중분류, 업종구분값을 구분자로 연결한 문자열이며 여기서 구분자는 '|'와 ';'입니다.
        예를들어 OpenAPI.KOA_Functions("GetMasterStockInfo", "039490")을 호출하면
        시장구분0|거래소;시장구분1|중형주;업종구분|금융업;
        이렇게 결과를 얻을 수 있습니다.

        4. 조검검색 종목코드와 현재가 수신(실시간 조건검색은 사용할수 없음)
        조건검색결과에 종목코드와 그 종목의 현재가를 함께 수신하는 방법이며
        실시간 조건검색에서는 사용할 수 없고 오직 조건검색에만 사용할수 있습니다.

        OpenAPI.KOA_Functions(_T("SetConditionSearchFlag"), _T("AddPrice")); // 현재가 포함하도록 설정
        현재가 포함으로 설정시 OnReceiveTrCondition()이벤트에
        "종목코드1^현재가1;종목코드2^현재가2;...종목코드n^현재가n"형식으로 전달됨

        OpenAPI.KOA_Functions(_T("SetConditionSearchFlag"), _T("DelPrice")); // 현재가 미포함 (원래상태로 전환)
        현재가 미포함시 기존처럼 "종목코드1^종목코드2...종목코드n" 형식으로 전달되므로
        설정에 따라 수신데이터 처리방법이 달라져야 하므로 주의하셔야 합니다.
        이 방법은 실시간 조건검색에서는 사용할 수 없고 수신데이터에 현재가가 포함되므로 데이터처리방법을 달리해야 합니다

        5. 업종코드 획득
        OpenAPI.KOA_Functions(_T("GetUpjongCode"), _T("0")); // 장내업종코드요청
        두 번째 인자로 사용할 수 있는 값은 0,1,2,4,7 이며
        0:장내, 1: 코스닥, 2:KOSPI200, 4:KOSPI100(KOSPI50), 7:KRX100 필요한 업종을 구별해서 사용하시면 됩니다.

        함수반환값은 "시장구분값,업종코드,업종명|시장구분값,업종코드,업종명|...|시장구분값,업종코드,업종명" 형식입니다.
        즉 하나의 업종코드는 입력한 시장구분값과 업종코드 그리고 그 업종명이 쉼표(,)로 구분되며 각 업종코드는 '|'로 구분됩니다.

        ------------------------------------------------------------------------------------------------------

        """
        return self.call("KOA_Functions(QString, QString)", function_name, str(arg))

    """
    Event Handlers
    """
    def on_event_connect(self, err_code):
        """
        # 개발가이드 > 로그인 버전처리

        [OnEventConnect()이벤트]

        OnEventConnect(
          long nErrCode   // 로그인 상태를 전달하는데 자세한 내용은 아래 상세내용 참고
        )

        로그인 처리 이벤트입니다. 성공이면 인자값 nErrCode가 0이며 에러는 다음과 같은 값이 전달됩니다.

        nErrCode별 상세내용
        -100 사용자 정보교환 실패
        -101 서버접속 실패
        -102 버전처리 실패
        """
        pass

    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        """
        # 개발가이드 > 로그인 버전처리, 조회와 실시간데이터처리, 주문과 잔고처리

        [OnReceiveMsg()이벤트]

        OnReceiveMsg(
          BSTR sScrNo,   // 화면번호
          BSTR sRQName,  // 사용자 구분명
          BSTR sTrCode,  // TR이름
          BSTR sMsg     // 서버에서 전달하는 메시지
        )

        서버통신 후 수신한 메시지를 알려줍니다.
        메시지에는 6자리 코드번호가 포함되는데 이 코드번호는 통보없이 수시로 변경될 수 있습니다.
        따라서 주문이나 오류관련처리를 이 코드번호로 분류하시면 안됩니다.
        """
        pass

    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next, *args):
        """
        # 개발가이드 > 조회와 실시간데이터처리, 주문과 잔고처리

        [OnReceiveTrData() 이벤트]

        void OnReceiveTrData(
          BSTR sScrNo,       // 화면번호
          BSTR sRQName,      // 사용자 구분명
          BSTR sTrCode,      // TR이름
          BSTR sRecordName,  // 레코드 이름
          BSTR sPrevNext,    // 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
          LONG nDataLength,  // 사용안함.
          BSTR sErrorCode,   // 사용안함.
          BSTR sMessage,     // 사용안함.
          BSTR sSplmMsg     // 사용안함.
        )

        조회요청 응답을 받거나 조회데이터를 수신했을때 호출됩니다.
        조회데이터는 이 이벤트내부에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.

        # 사용하지 않는 nDataLength, sErrorCode, sMessage, sSplmMsg은 묶어서 *args로 처리함
        """
        pass

    def on_receive_real_data(self, code, real_type, real_data):
        """
        # 개발가이드 > 조회와 실시간데이터처리

        [OnReceiveRealData()이벤트]

        OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 리얼타입
          BSTR sRealData    // 실시간 데이터 전문
        )

        실시간 데이터 수신할때마다 호출되며 SetRealReg()함수로 등록한 실시간 데이터도 이 이벤트로 전달됩니다.
        GetCommRealData()함수를 이용해서 실시간 데이터를 얻을수 있습니다.
        """
        pass

    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        # 개발가이드 > 주문과 잔고처리

        [OnReceiveChejanData() 이벤트]

        OnReceiveChejanData(
          BSTR sGubun, // 체결구분 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4'
          LONG nItemCnt,
          BSTR sFIdList
        )

        주문요청후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 호출되며 GetChejanData()함수를 이용해서 상세한 정보를 얻을수 있습니다.
        """
        pass

    def on_receive_condition_ver(self, ret, msg):
        """
        # 개발가이드 > 조건검색

        [OnReceiveConditionVer() 이벤트]

        OnReceiveConditionVer(
          LONG lRet, // 호출 성공여부, 1: 성공, 나머지 실패
          BSTR sMsg  // 호출결과 메시지
        )

        사용자 조건식요청에 대한 응답을 서버에서 수신하면 호출되는 이벤트입니다.

        ------------------------------------------------------------------------------------------------------

        [사용자 조건식 호출결과 수신예시]
        OnReceiveConditionVer(long lRet, LPCTSTR sMsg)
        {
          if(lRet != 0) return;

          CString strCondList(m_KOA.GetConditionNameList());
          CString strOneCond, strItemID, strCondName;
          while(AfxExtractSubString(strOneCond, strCondList, nIndex++, _T(';')))  // 조건식을 하나씩 분리한다.
          {
            if(strOneCond.IsEmpty()) continue;
            AfxExtractSubString(strItemID, strOneCond, 0, _T('^'));  // 조건명 인덱스를 분리한다.
            AfxExtractSubString(strCondName, strOneCond, 1, _T('^'));  // 조건식 이름을 분리한다.
          }
        }

        ------------------------------------------------------------------------------------------------------

        """
        pass

    def on_receive_tr_condition(self, scr_no, code_list, condition_name, index, next):
        """
        # 개발가이드 > 조건검색

        [OnReceiveTrCondition() 이벤트]

        OnReceiveTrCondition(
          BSTR sScrNo,    // 화면번호
          BSTR strCodeList,   // 종목코드 리스트
          BSTR strConditionName,    // 조건식 이름
          int nIndex,   // 조건명 인덱스
          int nNext   // 연속조회 여부
        )

        조건검색 요청으로 검색된 종목코드 리스트를 전달하는 이벤트입니다.
        종목코드 리스트는 각 종목코드가 ';'로 구분되서 전달됩니다.

        ------------------------------------------------------------------------------------------------------

        [조건검색 결과 수신예시]
        OnReceiveTrCondition(LPCTSTR sScrNo,LPCTSTR strCodeList, LPCTSTR strConditionName, int nIndex, int nNext)
        {
          if(strCodeList == "") return;
          CString strCode, strCodeName;
          int   nIdx = 0;
          while(AfxExtractSubString(strCode, strCodeList, nIdx++, _T(';')))// 하나씩 종목코드를 분리
          {
            if(strCode == _T("")) continue;
            strCodeName = OpenAPI.GetMasterCodeName(strCode); // 종목명을 가져온다.
          }
        }

        ------------------------------------------------------------------------------------------------------

        """
        pass

    def on_receive_real_condition(self, code, type, condition_name, condition_index):
        """
        # 개발가이드 > 조건검색

        [OnReceiveRealCondition() 이벤트]

        OnReceiveRealCondition(
          BSTR strCode,   // 종목코드
          BSTR strType,   //  이벤트 종류, "I":종목편입, "D", 종목이탈
          BSTR strConditionName,    // 조건식 이름
          BSTR strConditionIndex    // 조건명 인덱스
        )

        실시간 조건검색 요청으로 신규종목이 편입되거나 기존 종목이 이탈될때 마다 호출됩니다.

        ------------------------------------------------------------------------------------------------------

        [실시간 조건검색 수신예시]
        OnReceiveRealCondition(LPCTSTR sCode, LPCTSTR sType, LPCTSTR strConditionName, LPCTSTR strConditionIndex)
        {
          CString strCode(sCode), strCodeName;
          int   nIdx = 0;
          CString strType(sType);
          if(strType == _T("I"))// 종목편입
          {
            // 종목명을 가져온다.
            strCodeName = OpenAPI.GetMasterCodeName(strCode);
            // 실시간 시세등록
            long lRet = OpenAPI.SetRealReg(strSavedScreenNo, strCode, _T("9001;302;10;11;25;12;13"), "1");
          }
          else if(strType == _T("D")) // 종목이탈
          {
            OpenAPI.SetRealRemove(strSavedScreenNo, strCode);// 실시간 시세해지
          }
        }
          
        ------------------------------------------------------------------------------------------------------

        """
        pass
