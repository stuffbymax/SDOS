"""
name: SDOS
description: DOS Simulator
version: 0.0.1
author: martinP
license: not specified
"""

from osBoot import *
from boot_sim import *
from game_Pack import *
from sedit import *
from SBASIC import Interpreter
from time import sleep
import os
import time
import sys
import random
from random import randint


# variables
current_dir = ["C:\\"]  # store path segments in a list
version = "0.0.1"

# color  (colorama)
try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    class Dummy:
        RESET_ALL = ""
    Fore = Style = Dummy()


####    Fake File System    ####

FILES = {
    "C:\\": [
        ("AUTOEXEC.BAT", "2KB"),
        ("CONFIG.SYS", "1KB"),
        ("COMMAND.COM", "38KB"),
        ("GAMES", "<DIR>"),
        ("BIN", "<DIR>"),
    ],
    "C:\\GAMES": [
        ("SNAKE.C", "12KB"),
        ("ADVENTURE.C", "8KB"),
        ("GAMES.EXE", "20KB"),
    ],
    "C:\\BIN": [
        ("UTIL.EXE", "15KB"),
        ("NETSTAT.EXE", "10KB"),
    ],
    "A:\\": [
        ("README.TXT", "4KB"),
    ],
}

def SDOS_BANNER():
    banner = r"""
 _____                                     _____ 
( ___ )                                   ( ___ )
 |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | 
 |   |   ██████ ▓█████▄  ▒█████    ██████  |   | 
 |   | ▒██    ▒ ▒██▀ ██▌▒██▒  ██▒▒██    ▒  |   | 
 |   | ░ ▓██▄   ░██   █▌▒██░  ██▒░ ▓██▄    |   | 
 |   |   ▒   ██▒░▓█▄   ▌▒██   ██░  ▒   ██▒ |   | 
 |   | ▒██████▒▒░▒████▓ ░ ████▓▒░▒██████▒▒ |   | 
 |   | ▒ ▒▓▒ ▒ ░ ▒▒▓  ▒ ░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░ |   | 
 |   | ░ ░▒  ░ ░ ░ ▒  ▒   ░ ▒ ▒░ ░ ░▒  ░ ░ |   | 
 |   | ░  ░  ░   ░ ░  ░ ░ ░ ░ ▒  ░  ░  ░   |   | 
 |   |       ░     ░        ░ ░        ░   |   | 
 |   |           ░                         |   | 
 |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| 
(_____)                                   (____)
"""
    print(banner)


####    Functions    ####

def dos_intro():
    os.system("cls" if os.name == "nt" else "clear")
    SDOS_BANNER()
    print(Fore.GREEN + "CC DOS v5.3.12 [C] 1987-2025 CC Industries" + Style.RESET_ALL)
    print("All rights reserved.\n")
    time.sleep(0.8)
    print("Type HELP for a list of commands.\n")


def cmd_help():
    print("Available commands:")
    print("  DIR       - List directory contents")
    print("  CLS       - Clear the screen")
    print("  GAMES     - Launch games pack exe")
    print("  CD [dir]  - Change directory")
    print("  ECHO text - Print text to the screen")
    print("  RUN [file.SDOS]- Execute an S-BASIC script") 
    print("  VER       - Display DOS version")
    print("  TIME      - Display system time")
    print("  HELP      - Show this help message")
    print("  OS        - Display SDOS banner")
    print("  EXIT      - Exit DOS simulator")
    print("  PING      - Check network connectivity")
    print("  PI        - Do you like Pi?")


def cmd_dir(path):
    entries = FILES.get(path, [])
    print(f" Directory of {path}\n")
    for name, size in entries:
        time.sleep(0.05)
        print(f"{name:<20} {size:>8}")
    print()


def cmd_echo(args):
    print(" ".join(args))


def cmd_ver():
    print(f" SDOS Version {version}")


def cmd_time():
    t = time.strftime("%H:%M:%S")
    print(f"Current time: {t}")


def cmd_ping(args):
    if not args:
        print("Usage: PING [hostname]")
        return

    hostname = args[0]
    print(f"Pinging {hostname} with 32 bytes of data:")

    for i in range(4):
        time.sleep(0.5)
        latency = randint(20, 100)
        print(f"Reply from {hostname}: bytes=32 time={latency}ms TTL=64")

    print("\nPing statistics for {}:".format(hostname))
    print("    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),")
    print("Approximate round trip times in milli-seconds:")
    print("    Minimum = 20ms, Maximum = 100ms, Average = {}ms".format((20 + 100) // 2))

def cmd_pi():
    pi_digits = "3.14159265358979323846264338327950288419716939937510"
    print("Pi to 50 decimal places:")
    print(pi_digits)

def dos_loop():
    while True:
        try:
            cmd_line = input(Fore.GREEN + f"{current_dir[0]}>" + Style.RESET_ALL)
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not cmd_line.strip():
            continue

        parts = cmd_line.strip().split()
        cmd = parts[0].upper()
        args = parts[1:]

        if cmd == "HELP":
            cmd_help()
        elif cmd == "DIR":
            cmd_dir(current_dir[0])
        elif cmd == "CLS":
            os.system("cls" if os.name == "nt" else "clear")
        elif cmd == "ECHO":
            cmd_echo(args)
        elif cmd == "VER":
            cmd_ver()
        elif cmd == "TIME":
            cmd_time()
        elif cmd == "GAMES":
            games_menu()
        elif cmd == "OS":
            SDOS_BANNER()
        elif cmd == "PING":
            cmd_ping(args)
        elif cmd == "PI":
            cmd_pi()
        elif cmd == "SEDIT":
            sedit()
        elif cmd == "CD":
            if not args:
                print(f"Current directory: {current_dir[0]}")
                print("Usage: CD [directory or drive]")
            else:
                target = args[0].upper()

                # Switch to a different drive
                if len(target) == 2 and target[1] == ":":
                    drive_path = f"{target}\\"
                    if drive_path in FILES:
                        current_dir[0] = drive_path
                    else:
                        print(f"The system cannot find the drive {target}")
                elif target == "\\":
                    # Go to root of current drive
                    current_dir[0] = current_dir[0][0] + ":\\"
                elif target == "..":
                    # Move up one directory
                    parts = current_dir[0].rstrip("\\").split("\\")
                    if len(parts) > 1:
                        current_dir[0] = "\\".join(parts[:-1]) + "\\"
                    else:
                        print("Already at root directory.")
                else:
                    # Subdirectory of current path
                    new_path = current_dir[0].rstrip("\\") + "\\" + target  # build path without extra trailing slash
                    if new_path in FILES:
                        current_dir[0] = new_path
                    else:
                        print("The system cannot find the path specified.")
        elif cmd == "RUN":
            if not args:
                print("Usage: RUN [filename.SDOS]")
            else:
                filename = args[0].upper()
                if not filename.endswith(".SDOS"):
                    print("Error: RUN command only supports .SDOS files.")
                else:
                    script_found = False
                    for f in FILES.get(current_dir[0], []):
                        if f["name"].upper() == filename:
                            script_found = True
                            print(f"Running {filename}...\n")
                            print(f"Simulated execution:\n{f['content']}\n")
                            print(f"Script {filename} finished.\n")
                            break
                    if not script_found:
                        print(f"Error: File '{filename}' not found in current directory.")
        elif cmd == "EXIT":
            print("System halted.")
            time.sleep(1)
            break
        else:
            print(f"'{cmd}' is not recognized as an internal or external command.")


####    Run    ####
if __name__ == "__main__":
    dos_intro()
    dos_loop()
