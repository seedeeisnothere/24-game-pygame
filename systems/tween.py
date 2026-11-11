# Easing functions: t goes from 0 to 1 and returns a value from 0 to 1.

# Starts fast, slows down at the end.
def ease_out(t, power=3):
    return 1 - (1 - t) ** power


# Starts slow, speeds up at the end.
def ease_in(t, power=3):
    return t ** power
