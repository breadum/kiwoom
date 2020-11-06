# Tutorials
Python wrapper of Kiwoom Open API+

## Library Structure

#### Class Kiwoom 

> 키움 Open API+  활용을 위한 메인 클래스  

   - API methods
   
         KOA Studio 개발가이드 확인
   
   - loop ()  /  unloop ()
         
         다음 코드 실행 대기/해제를 위한 루프 기능
      
   - connect (event, signal, slot) 
   
         Event와 Signal, Slot 메서드를 연결해 이벤트 발생 시 자동 호출
   
   - set_connect_hook / remove_connect_hook 
   
         한 가지 이벤트에 여러가지 Slot을 연결할 때 
   
   
   
#### Class API

> 부가 기능이 없는 키움 Open API+

   - Kiwoom Open API methods
   
#### Package config

> 여러가지 설정들이 저장된 패키지 
   
   - events : 이벤트 핸들러
   
   - markets : 시장
   
   - sectors : 섹터
   
   - market_gubun : 시장구분

## Tutorial Contents

0. Baisc Structure
1. 