import json


class Actions:
    SHOW_TOAST = "show-toast"
    COPY = "copy"
    ADD_PARAM = "add-param"
    OPEN_URL = "open-url"


def slapdash_show_message_and_exit(msg: str) -> None:
    """
    Useful for showing error messages
    """
    print(json.dumps({"view": msg}))
    exit()
