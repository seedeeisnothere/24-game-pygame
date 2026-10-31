def ease_out(t, power=3):
    return 1 - (1 - t) ** power

def ease_in(t, power=3):
    return t ** power