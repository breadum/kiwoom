from kiwoom.config.error import msg


class Slot:
    def __init__(self, api):
        self.api = api

    def history(self):
        pass

    def histories(self):
        pass

    """
    Default slots to the most basic two events.
        on_event_connect
        on_receive_msg
    """
    # Default event slot for on_event_connect
    def on_event_connect(self, err_code):
        """
        Default slot for 'on_event_connect'

        When on_event_connect is called, this method automatically will be called.
        """
        print(f'\n로그인 {msg(err_code)}')
        print(f'\n* 시스템 점검\n  - 월 ~ 토 : 05:05 ~ 05:10\n  - 일 : 04:00 ~ 04:30\n')
        self.unloop()

    # Default event slot for on_receive_msg_slot
    def on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        """
        Default slot for 'on_receive_msg'

        Whenever the server sends a message, this method prints depending on below.
        >> Kiwoom.message(True)
        >> Kiwoom.message(False)
        """
        if self.api.msg:
            print(f'\n화면번호: {scr_no}, 요청이름: {rq_name}, TR코드: {tr_code} \n{msg}\n')
