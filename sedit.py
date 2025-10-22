"""
Simple curses-based editor for SBASIC files.

Features:
- Open and edit a file (default: `sbesic`)
- Save (Ctrl-S), Quit (Ctrl-Q), Run with SBASIC interpreter (Ctrl-R)
- Basic navigation: arrows, PageUp/PageDown, Home/End
- Basic syntax highlighting for a few SBASIC keywords

Designed to be small and dependency-light. On Windows install `windows-curses`.
"""
from __future__ import annotations

import curses
import os
import sys
import subprocess
import locale
from typing import List

locale.setlocale(locale.LC_ALL, '')

CTRL_S = 19
CTRL_Q = 17
CTRL_R = 18

KEYWORDS = [
    'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'GOTO', 'GOSUB', 'RETURN',
    'FOR', 'TO', 'STEP', 'NEXT', 'INPUT', 'DIM', 'END', 'REM'
]


class Editor:
    def __init__(self, stdscr, filename: str):
        self.stdscr = stdscr
        self.filename = filename
        self.lines: List[str] = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.view_x = 0
        self.view_y = 0
        self.modified = False
        self.message = ''
        self._init_colors()
        self.load_file()

    def _init_colors(self):
        curses.use_default_colors()
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_YELLOW, -1)  # keyword
            curses.init_pair(2, curses.COLOR_GREEN, -1)   # string
            curses.init_pair(3, curses.COLOR_CYAN, -1)    # number
            curses.init_pair(4, curses.COLOR_MAGENTA, -1) # comment/REM

    def load_file(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8', errors='replace') as f:
                self.lines = [ln.rstrip('\n') for ln in f.readlines()]
        else:
            self.lines = ['']

    def save_file(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines) + '\n')
            self.modified = False
            self.set_message(f"Saved {self.filename}")
        except Exception as e:
            self.set_message(f"Save error: {e}")

    def set_message(self, msg: str):
        self.message = msg

    def run_file(self):
        # Run SBASIC interpreter (sbesic.py) with the current file
        interp = os.path.join(os.path.dirname(__file__), 'sbesic.py')
        if not os.path.exists(interp):
            self.set_message('sbesic.py not found in project root')
            return
        try:
            # flush to make sure file saved first
            if self.modified:
                self.save_file()
            self.set_message('Running... (output in terminal)')
            # spawn a subprocess to run and attach to same terminal
            subprocess.run([sys.executable, interp, self.filename])
            self.set_message('Run finished')
        except Exception as e:
            self.set_message(f'Run error: {e}')

    def draw(self):
        self.stdscr.erase()
        rows, cols = self.stdscr.getmaxyx()

        # top status
        status = f"{self.filename} - {'modified' if self.modified else 'saved'}  Ln {self.cursor_y+1}, Col {self.cursor_x+1}"
        if len(status) > cols - 1:
            status = status[:cols-1]
        try:
            self.stdscr.addstr(0, 0, status, curses.A_REVERSE)
        except curses.error:
            pass

        # visible area
        top = 1
        bottom = rows - 2
        height = max(1, bottom - top + 1)

        # ensure view_y in range
        if self.cursor_y < self.view_y:
            self.view_y = self.cursor_y
        elif self.cursor_y >= self.view_y + height:
            self.view_y = self.cursor_y - height + 1

        # draw lines with line numbers
        gutter_w = 6
        for i in range(height):
            ln_no = self.view_y + i
            y = top + i
            if ln_no >= len(self.lines):
                continue
            line = self.lines[ln_no]
            # draw gutter
            gutter = f"{ln_no+1:>4} "
            try:
                self.stdscr.addstr(y, 0, gutter, curses.color_pair(0))
            except curses.error:
                pass

            # draw line with simple highlighting
            self._draw_line(y, gutter_w, cols - gutter_w, line)

        # bottom message bar
        msg = self.message or "Ctrl-S Save  Ctrl-R Run  Ctrl-Q Quit"
        try:
            self.stdscr.addstr(rows-1, 0, msg[:cols-1], curses.A_REVERSE)
        except curses.error:
            pass

        # set cursor
        curs_y = 1 + (self.cursor_y - self.view_y)
        curs_x = self.cursor_x - self.view_x + gutter_w
        try:
            self.stdscr.move(curs_y, max(gutter_w, curs_x))
        except curses.error:
            # ignore move errors when off-screen
            pass

        self.stdscr.refresh()

    def _draw_line(self, y: int, x: int, maxw: int, line: str):
        # naive tokenization: detect REM (comment) and strings, then keywords
        col = x
        if line.strip().upper().startswith('REM'):
            try:
                self.stdscr.addstr(y, col, line[:maxw], curses.color_pair(4))
            except curses.error:
                pass
            return

        i = 0
        in_str = False
        while i < len(line) and col < x + maxw:
            ch = line[i]
            if ch == '"':
                # string region
                j = i+1
                while j < len(line) and line[j] != '"':
                    j += 1
                j = min(j, len(line)-1)
                segment = line[i:j+1]
                try:
                    self.stdscr.addstr(y, col, segment[:x+maxw-col], curses.color_pair(2))
                except curses.error:
                    pass
                col += len(segment)
                i = j+1
                continue

            # check keywords (word boundaries)
            if ch.isalpha():
                j = i
                while j < len(line) and (line[j].isalnum() or line[j]=='_'):
                    j += 1
                word = line[i:j]
                if word.upper() in KEYWORDS:
                    try:
                        self.stdscr.addstr(y, col, word, curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    try:
                        self.stdscr.addstr(y, col, word)
                    except curses.error:
                        pass
                col += len(word)
                i = j
                continue

            # default
            try:
                self.stdscr.addstr(y, col, ch)
            except curses.error:
                pass
            col += 1
            i += 1

    def insert_char(self, ch: str):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x += len(ch)
        self.modified = True

    def newline(self):
        line = self.lines[self.cursor_y]
        left = line[:self.cursor_x]
        right = line[self.cursor_x:]
        self.lines[self.cursor_y] = left
        self.lines.insert(self.cursor_y+1, right)
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True

    def backspace(self):
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified = True
        elif self.cursor_y > 0:
            prev = self.lines[self.cursor_y-1]
            cur = self.lines[self.cursor_y]
            self.cursor_x = len(prev)
            self.lines[self.cursor_y-1] = prev + cur
            del self.lines[self.cursor_y]
            self.cursor_y -= 1
            self.modified = True

    def delete_char(self):
        line = self.lines[self.cursor_y]
        if self.cursor_x < len(line):
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x+1:]
            self.modified = True
        elif self.cursor_y < len(self.lines)-1:
            # join next line
            self.lines[self.cursor_y] = line + self.lines[self.cursor_y+1]
            del self.lines[self.cursor_y+1]
            self.modified = True

    def handle_key(self, key):
        if key == CTRL_S:
            self.save_file()
        elif key == CTRL_Q:
            if self.modified:
                self.set_message('Unsaved changes - press Ctrl-Q again to quit without saving')
                self.modified = self.modified  # no-op, message only
                # require second Ctrl-Q to actually quit
                return 'confirm_quit'
            return 'quit'
        elif key == CTRL_R:
            self.run_file()
        elif key in (curses.KEY_LEFT,):
            if self.cursor_x > 0:
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = len(self.lines[self.cursor_y])
        elif key in (curses.KEY_RIGHT,):
            if self.cursor_x < len(self.lines[self.cursor_y]):
                self.cursor_x += 1
            elif self.cursor_y < len(self.lines)-1:
                self.cursor_y += 1
                self.cursor_x = 0
        elif key in (curses.KEY_UP,):
            if self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key in (curses.KEY_DOWN,):
            if self.cursor_y < len(self.lines)-1:
                self.cursor_y += 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key in (curses.KEY_NPAGE,):
            rows, _ = self.stdscr.getmaxyx()
            self.cursor_y = min(len(self.lines)-1, self.cursor_y + (rows//2))
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key in (curses.KEY_PPAGE,):
            rows, _ = self.stdscr.getmaxyx()
            self.cursor_y = max(0, self.cursor_y - (rows//2))
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key in (curses.KEY_HOME,):
            self.cursor_x = 0
        elif key in (curses.KEY_END,):
            self.cursor_x = len(self.lines[self.cursor_y])
        elif key in (curses.KEY_DC,):
            self.delete_char()
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.backspace()
        elif key == 10 or key == 13:  # Enter
            self.newline()
        elif 0 <= key <= 255:
            ch = chr(key)
            if ch.isprintable():
                self.insert_char(ch)

    def run(self):
        confirm_quit = False
        while True:
            self.draw()
            key = self.stdscr.getch()
            res = self.handle_key(key)
            if res == 'confirm_quit':
                # wait for another Ctrl-Q
                k2 = self.stdscr.getch()
                if k2 == CTRL_Q:
                    return
                else:
                    self.set_message('Quit aborted')
            elif res == 'quit':
                return


def sedit():
    # on Windows, curses isn't included; the user should install windows-curses
    try:
        import curses  # noqa: F401
    except Exception:
        print('curses not available. On Windows run: pip install windows-curses')
        sys.exit(1)

    filename = sys.argv[1] if len(sys.argv) > 1 else 'sbesic'

    def wrapped(stdscr):
        # configure
        curses.raw()
        stdscr.keypad(True)
        curses.curs_set(1)
        ed = Editor(stdscr, filename)
        ed.run()

    curses.wrapper(wrapped)


if __name__ == '__main__':
    sedit()
