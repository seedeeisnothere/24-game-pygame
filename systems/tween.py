def ease_out(t):
    return 1 - (1 - t) ** 3

def ease_in(t):
    return t ** 3