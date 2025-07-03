# Tutorials
Simple Python Wrapper for Kiwoom Open API+

## Library Structure 

#### Class API

> 부가 기능이 없는 키움 Open API+

   - API methods

#### Class Kiwoom 

> 키움 Open API+  활용을 위한 메인 클래스  

   - API methods
   
         KOA Studio 개발가이드 확인
   
   - loop() & unloop()
         
         다음 코드 실행 대기/해제를 위한 루프 기능
      
   - connect(event, signal, slot) 
   
         Event와 Signal, Slot 메서드를 연결해 이벤트 발생 시 자동 호출
   
   - set_connect_hook(event, param) & remove_connect_hook(event) 
   
         한 가지 이벤트에 여러가지 Slot을 연결할 때, 이벤트에 입력되는 특정 인자값을 기준으로 연결되도록 설정 
   
#### Class Bot

> 서버에 요청하기 위한 클래스  

   - login()
   
         로그인 함수
   
   - histories()
         
         시장 데이터 다운로드 함수

#### Class Bot

> 서버에서 데이터를 받아 처리하기 위한 클래스

   - login()
   
         Bot.login()을 통해 로그인에 대한 서버 응답 처리 함수
   
   - histories()
         
         Bot.histories()를 통해 서버에서 보낸 시장 데이터 처리 함수 
   
#### Package config

> 여러가지 설정들이 저장된 패키지로 Print 함수를 통해 확인 가능 
   
   - EVENTS
   
         API에 정의된 이벤트 핸들러 8가지로 자세한 사항은 KOA Studio 참고
   
   - MARKETS, MARKET_GUBUNS, SECTORS
    
         API에 입력값으로 사용되는 시장, 시장구분, 섹터 모음
   

## Tutorial Contents

#### 1. Basic Structure

- 모듈을 활용할 수 있는 기본적인 프로그램 구현 패턴 소개 

#### 2. Login

- 모듈을 이용한 키움 서버 로그인 예시

#### 3. Historical Data

- 모듈을 이용해 시장 데이터 다운로드 예시

#### 4. Account

- 간단 API 함수를 활용한 계좌번호 조회 예시

#### 5. TR Data

- 계좌 잔고 조회를 통한 TR 데이터 요청 및 수신 예시 
- connect, set_connect_hook, comm_rq_data, on_receive_tr_data 활용

#### 6. Trading

- 주문 전송 및 체결 정보 수신 예시

#### 7. Trading Records

- 거래내역 조회 및 엑셀 저장 예시 (영웅문 0343 화면)
