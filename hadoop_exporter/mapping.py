
def fsstate(value):
    if value == "Operational":
        return 0.0
    elif value == "Safemode":
        return 1.0
    else:
        return 9999.0


def hastate(value):
    if value == "initializing":
        return 0.0
    elif value == "active":
        return 1.0
    elif value == "standby":
        return 2.0
    elif value == "stopping":
        return 3.0
    else:
        return 9999
