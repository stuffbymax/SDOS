"""
Boot Simulator
__author0__ = "Riley Porter-Reed"
__version__ = "0.0.1"
"""

####    Imports    ####

from osBoot import *
from time import sleep
import os
import time
import sys
import random
from random import randint


####    Variables    ####

userInput = ""


####    Classes    ####



####    Functions    ####

def animate_dots(full_line, delay=0.1):
    # Split the line into left, dots, and right text
    if "..." in full_line:
        # Find the index where dots begin
        dot_start = full_line.find(".")
        left_part = full_line[:dot_start].rstrip()
        right_part = full_line[dot_start:].lstrip()

        # Determine number of dots (count consecutive '.'s)
        dot_count = 0
        for c in right_part:
            if c == '.':
                dot_count += 1
            else:
                break

        # Separate the trailing text (after dots)
        trailing_text = right_part[dot_count:].strip()

        # Animate dots
        sys.stdout.write(left_part + " ")
        sys.stdout.flush()
        for i in range(dot_count):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(" " + trailing_text + "\n")
        sys.stdout.flush()
    else:
        print(full_line)


def bootUp():
    os.system("cls" if os.name == "nt" else "clear")

    base_delay = 0.6   # starting delay between lines
    min_delay = 0.3  # fastest delay
    acceleration = 0.92  # higher = slower acceleration (0.92 = 8% faster each line)

    for line in osBootSequence:
        if not line.strip():
            print()
            time.sleep(0.1)
            continue

        if "POST COMPLETE" in line:
            for char in line:
                print(char, end="", flush=True)
                time.sleep(0.01)
            print("\n")
            time.sleep(0.5)

        elif "..." in line or "....." in line:
            # Animate dots within the line
            animate_dots(line, delay=max(0.02, base_delay / 4))
            time.sleep(base_delay / 2)
        else:
            print(line)
            time.sleep(base_delay)

        # Speed up each line
        base_delay = max(min_delay, base_delay * acceleration)


####    Code    ####

bootUp()

   







