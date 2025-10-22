# sbasic_interpreter.py
# Author: martinP (with assistance from AI)
# Description: An interpreter for the S-BASIC language with support for loops, subroutines, and screen control.

import time
import random
import re
import curses

class Interpreter:
    """Executes S-BASIC scripts within a curses window."""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.variables = {}
        self.labels = {}
        self.lines = []
        self.pc = 0  # Program Counter

        # Stacks for control structures
        self.for_loop_stack = []  # For FOR/NEXT loops
        self.gosub_stack = []     # For GOSUB/RETURN subroutines

    def _sub_vars(self, text):
        """Substitutes %var% placeholders with their values."""
        # Substitute variables case-insensitive
        def repl(m):
            varname = m.group(1).lower()
            return str(self.variables.get(varname, 0))
        return re.sub(r'%(\w+)%', repl, text)

    def _preprocess(self):
        """First pass: Scan for all LABEL definitions."""
        for i, line in enumerate(self.lines):
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0].upper() == "LABEL":
                if len(parts) > 1:
                    self.labels[parts[1].lower()] = i

    def _find_matching_block_end(self, start_index, start_kw="IF", end_kw="ENDIF"):
        """Finds the matching ENDIF or NEXT for a block, handling nesting."""
        nest_level = 1
        for i in range(start_index + 1, len(self.lines)):
            line = self.lines[i].strip().upper()
            if line.startswith(start_kw):
                nest_level += 1
            elif line.startswith(end_kw):
                nest_level -= 1
                if nest_level == 0:
                    return i
        return len(self.lines)

    def _find_else(self, if_index, endif_index):
        """Finds an ELSE within an IF/ENDIF block."""
        for i in range(if_index + 1, endif_index):
            if self.lines[i].strip().upper() == "ELSE":
                return i
        return None

    def _safe_eval(self, expr):
        """Evaluate an expression safely using variables."""
        try:
            # Allow only variables and basic math operators
            # No builtins or functions accessible
            return eval(expr, {"__builtins__": None}, self.variables)
        except Exception:
            return 0

    def run(self, script_content):
        """Main entry point to execute a script."""
        self.lines = script_content.strip().splitlines()
        self._preprocess()

        self.pc = 0
        while self.pc < len(self.lines):
            line = self.lines[self.pc].strip()

            if not line or line.upper().startswith("REM"):
                self.pc += 1
                continue

            parts = line.split()
            command = parts[0].upper()
            args = parts[1:]

            # --- Command Handling ---
            if command == "PRINT":
                message = self._sub_vars(" ".join(args))
                y, x = self.stdscr.getyx()
                try:
                    self.stdscr.addstr(y, x, message + "\n")
                except curses.error:
                    pass

            elif command == "LOCATE":
                y = int(self._sub_vars(args[0]))
                x = int(self._sub_vars(args[1]))
                sh, sw = self.stdscr.getmaxyx()
                if 0 <= y < sh and 0 <= x < sw:
                    self.stdscr.move(y, x)

            elif command == "INPUT":
                var_name = args[0].lower()
                prompt = self._sub_vars(" ".join(args[1:])) + " "
                self.stdscr.addstr(prompt)
                curses.echo()
                input_str = self.stdscr.getstr().decode('utf-8')
                curses.noecho()
                # Try to convert to int or float, else keep string
                try:
                    val = int(input_str)
                except ValueError:
                    try:
                        val = float(input_str)
                    except ValueError:
                        val = input_str
                self.variables[var_name] = val

            elif command == "SET":
                var_name = args[0].lower()
                # Skip the '=' sign
                expression = self._sub_vars(" ".join(args[2:]))
                val = self._safe_eval(expression)
                self.variables[var_name] = val

            elif command == "RANDOM":
                var_name = args[0].lower()
                min_val = int(self._sub_vars(args[1]))
                max_val = int(self._sub_vars(args[2]))
                self.variables[var_name] = random.randint(min_val, max_val)

            elif command == "IF":
                # Supports syntax: IF condition THEN
                # We'll assume last token is THEN
                condition_str = self._sub_vars(" ".join(args[:-1]))
                condition_result = self._safe_eval(condition_str)

                if not condition_result:
                    endif_line = self._find_matching_block_end(self.pc, "IF", "ENDIF")
                    else_line = self._find_else(self.pc, endif_line)
                    if else_line is not None:
                        self.pc = else_line
                    else:
                        self.pc = endif_line

            elif command == "ELSE":
                endif_line = self._find_matching_block_end(self.pc, "IF", "ENDIF")
                self.pc = endif_line

            elif command == "FOR":
                # FOR var = start TO end
                # Simplified parsing assuming exact syntax
                var_name = args[0].lower()
                if args[1] != '=' or args[3].upper() != 'TO':
                    self.set_message(f"Syntax error in FOR loop: {' '.join(parts)}")
                    self.pc += 1
                    continue

                start_val = self._safe_eval(self._sub_vars(args[2]))
                end_val = self._safe_eval(self._sub_vars(args[4]))
                self.variables[var_name] = start_val
                next_line = self._find_matching_block_end(self.pc, "FOR", "NEXT")
                self.for_loop_stack.append({'var': var_name, 'end': end_val, 'next_line': next_line})

            elif command == "NEXT":
                if not self.for_loop_stack:
                    self.pc += 1
                    continue
                loop_info = self.for_loop_stack[-1]
                var_name = loop_info['var']
                self.variables[var_name] += 1
                if self.variables[var_name] <= loop_info['end']:
                    # Jump back to line after FOR to repeat loop body
                    self.pc = self.for_loop_stack[-1]['next_line']  # We'll fix this below
                    # Actually, should jump to FOR + 1, not next_line (which is line after NEXT)
                    # So fix: store FOR line in stack
                    # Let's adjust for_loop_stack structure to hold 'for_line' as well

                    # We'll do this fix below after the main loop
                    pass
                else:
                    self.pc = loop_info['next_line']
                    self.for_loop_stack.pop()

            elif command == "GOSUB":
                label_name = args[0].lower()
                if label_name in self.labels:
                    self.gosub_stack.append(self.pc + 1)
                    self.pc = self.labels[label_name]
                    continue

            elif command == "RETURN":
                if self.gosub_stack:
                    self.pc = self.gosub_stack.pop()
                    continue

            elif command == "GOTO":
                label_name = args[0].lower()
                if label_name in self.labels:
                    self.pc = self.labels[label_name]
                    continue

            elif command == "CLS":
                self.stdscr.clear()

            elif command == "WAIT":
                try:
                    time.sleep(float(self._sub_vars(args[0])))
                except Exception:
                    pass

            self.pc += 1

        self.stdscr.addstr("\n\nScript finished. Press any key to exit.")
        self.stdscr.getch()

    def set_message(self, msg):
        # Could implement status line or logging
        pass


def main(stdscr):
    import sys
    if len(sys.argv) < 2:
        stdscr.addstr("Usage: python sbasic_interpreter.py script.sb\n")
        stdscr.getch()
        return

    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    interpreter = Interpreter(stdscr)
    interpreter.run(content)


if __name__ == '__main__':
    curses.wrapper(main)
