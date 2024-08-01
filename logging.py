# TODO make it better

unsent_loglines = []

def log(log_line: str) -> None:
    print(log_line)
    unsent_loglines.append(log_line)

def get_unsent_loglines() -> list:
    global unsent_loglines
    loglines = unsent_loglines
    unsent_loglines = []
    return loglines
