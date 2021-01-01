from kiwoom.config.const import events


def valid_event(event):
    """
    Returns True if event is valid, else False.

    :param event: str
        One of the pre-defined event names in string.
    :return: bool
    """
    if event not in events:
        print(f"{event} is not a valid event.\nSelect one of {events}.")
        return False
    return True
