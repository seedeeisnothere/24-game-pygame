import os
import sys

# When packaged as a .app (PyInstaller), assets/ and data/ live inside the
# bundle, so switch to that folder before the game loads any relative paths.
if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

import game


# Entry point: run this file to start the game.
if __name__ == "__main__":
    game.main()
