# Tutorials
Simple Python Wrapper for Kiwoom Open API+

## Library Structure 

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
   
#### Class API

> 부가 기능이 없는 키움 Open API+

   - API methods
   
#### Package config

> 여러가지 설정들이 저장된 패키지로 Print 함수를 통해 확인 가능 
   
   - events
   
         API에 정의된 이벤트 핸들러 8가지로 자세한 사항은 KOA Studio 참고
   
   - markets, market_gubuns, sectors
    
         API에 입력값으로 사용되는 시장, 시장구분, 섹터 모음
   

## Tutorial Contents

#### 1. Basic Structure

- 모듈을 활용할 수 있는 기본적인 프로그램 구현 패턴 소개 

#### 2. Login

- 모듈을 이용한 키움 서버 로그인 예시

#### 3. Account

- 간단 API 함수를 활용한 계좌번호 조회 예시

#### 4. TR Data

- 계좌 잔고 조회를 통한 TR 데이터 요청 및 수신 예시 
- connect, set_connect_hook, comm_rq_data, on_receive_tr_data 활용