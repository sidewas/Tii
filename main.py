#!/usr/bin/env python3
"""
Tii Language Interpreter
A cursed stack-based language where everything is Tii and i.
"""

import sys
import re
from collections import defaultdict


class TiiInterpreter:
    def __init__(self):
        self.stack = []
        self.vars = defaultdict(int)
        self.pc = 0
        self.tokens = []
        self.loop_stack = []  # for loop start positions

    def tokenize(self, code):
        """Tokenize: split into 'Tii' and 'i' and other words."""
        # Split by whitespace
        raw = code.split()
        tokens = []
        for word in raw:
            # Check if word is all 'i's
            if word == 'Tii':
                tokens.append('Tii')
            elif re.fullmatch(r'i+', word):
                tokens.append(('i_count', len(word)))
            elif word == 'Tii' + 'i' * len(word[3:]):
                # Handle cases like "Tiiii" - split into Tii + i's
                tokens.append('Tii')
                tokens.append(('i_count', len(word) - 3))
            else:
                # Unknown token, treat as comment/ignore
                pass
        return tokens

    def parse_instruction(self, token_idx):
        """Parse instruction starting at token_idx. Returns (instruction, consumed)."""
        if token_idx >= len(self.tokens):
            return ('eof',), 0

        # Count consecutive Tii tokens
        tii_count = 0
        i_count = 0
        idx = token_idx

        while idx < len(self.tokens):
            if self.tokens[idx] == 'Tii':
                tii_count += 1
                idx += 1
            elif isinstance(self.tokens[idx], tuple) and self.tokens[idx][0] == 'i_count':
                i_count = self.tokens[idx][1]
                idx += 1
                break
            else:
                break

        return (tii_count, i_count), idx - token_idx

    def run(self, code):
        self.tokens = self.tokenize(code)
        self.pc = 0
        self.loop_stack = []

        while self.pc < len(self.tokens):
            instr, consumed = self.parse_instruction(self.pc)
            self.pc += consumed

            if instr == ('eof',):
                break

            tii_count, i_count = instr

            # push N: 1 Tii + N i's
            if tii_count == 1 and i_count > 0:
                self.stack.append(i_count)

            # add: 2 Tii + 1 i
            elif tii_count == 2 and i_count == 1:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on add")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)

            # sub: 2 Tii + 2 i's
            elif tii_count == 2 and i_count == 2:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on sub")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(b - a)

            # mul: 2 Tii + 3 i's
            elif tii_count == 2 and i_count == 3:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on mul")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)

            # div: 2 Tii + 4 i's
            elif tii_count == 2 and i_count == 4:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on div")
                b = self.stack.pop()
                a = self.stack.pop()
                if a == 0:
                    raise RuntimeError("Division by zero")
                self.stack.append(b // a)

            # dup: 3 Tii + 1 i
            elif tii_count == 3 and i_count == 1:
                if not self.stack:
                    raise RuntimeError("Stack underflow on dup")
                self.stack.append(self.stack[-1])

            # swap: 3 Tii + 2 i's
            elif tii_count == 3 and i_count == 2:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on swap")
                self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

            # drop: 3 Tii + 3 i's
            elif tii_count == 3 and i_count == 3:
                if not self.stack:
                    raise RuntimeError("Stack underflow on drop")
                self.stack.pop()

            # print_int: 4 Tii + 1 i
            elif tii_count == 4 and i_count == 1:
                if not self.stack:
                    raise RuntimeError("Stack underflow on print_int")
                print(self.stack.pop(), end='')

            # print_char: 4 Tii + 2 i's
            elif tii_count == 4 and i_count == 2:
                if not self.stack:
                    raise RuntimeError("Stack underflow on print_char")
                print(chr(self.stack.pop()), end='')

            # loop_start: 5 Tii + 1 i
            elif tii_count == 5 and i_count == 1:
                if not self.stack:
                    raise RuntimeError("Stack underflow on loop_start")
                if self.stack[-1] == 0:
                    # Skip to matching loop_end
                    depth = 1
                    while depth > 0 and self.pc < len(self.tokens):
                        instr2, consumed2 = self.parse_instruction(self.pc)
                        if instr2 != ('eof',):
                            tc, ic = instr2
                            if tc == 5 and ic == 1:
                                depth += 1
                            elif tc == 5 and ic == 2:
                                depth -= 1
                        self.pc += consumed2
                else:
                    self.loop_stack.append(self.pc)

            # loop_end: 5 Tii + 2 i's
            elif tii_count == 5 and i_count == 2:
                if self.loop_stack:
                    self.pc = self.loop_stack[-1]

            # if_start: 6 Tii + 1 i
            elif tii_count == 6 and i_count == 1:
                if not self.stack:
                    raise RuntimeError("Stack underflow on if")
                if self.stack.pop() == 0:
                    # Skip to else or endif
                    depth = 1
                    while depth > 0 and self.pc < len(self.tokens):
                        instr2, consumed2 = self.parse_instruction(self.pc)
                        if instr2 != ('eof',):
                            tc, ic = instr2
                            if tc == 6 and ic == 1:
                                depth += 1
                            elif tc == 6 and ic == 2:
                                depth -= 1
                                if depth == 0:
                                    break
                            elif tc == 6 and ic == 3:
                                depth -= 1
                                if depth == 0:
                                    break
                        self.pc += consumed2

            # else_jump: 6 Tii + 2 i's
            elif tii_count == 6 and i_count == 2:
                # Skip to endif
                depth = 1
                while depth > 0 and self.pc < len(self.tokens):
                    instr2, consumed2 = self.parse_instruction(self.pc)
                    if instr2 != ('eof',):
                        tc, ic = instr2
                        if tc == 6 and ic == 1:
                            depth += 1
                        elif tc == 6 and ic == 3:
                            depth -= 1
                    self.pc += consumed2

            # if_end: 6 Tii + 3 i's
            elif tii_count == 6 and i_count == 3:
                pass  # nothing to do

            # eq: 7 Tii + 1 i
            elif tii_count == 7 and i_count == 1:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on eq")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a == b else 0)

            # lt: 7 Tii + 2 i's
            elif tii_count == 7 and i_count == 2:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on lt")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a < b else 0)

            # gt: 7 Tii + 3 i's
            elif tii_count == 7 and i_count == 3:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on gt")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a > b else 0)

            # input: 7 Tii + 4 i's
            elif tii_count == 7 and i_count == 4:
                try:
                    val = int(input())
                    self.stack.append(val)
                except:
                    self.stack.append(0)

            # store: 7 Tii + 5 i's
            elif tii_count == 7 and i_count == 5:
                if len(self.stack) < 2:
                    raise RuntimeError("Stack underflow on store")
                val = self.stack.pop()
                addr = self.stack.pop()
                self.vars[addr] = val

            # load: 7 Tii + 6 i's
            elif tii_count == 7 and i_count == 6:
                if not self.stack:
                    raise RuntimeError("Stack underflow on load")
                addr = self.stack.pop()
                self.stack.append(self.vars[addr])

            # Unknown instruction
            else:
                pass


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
    else:
        code = sys.stdin.read()

    interp = TiiInterpreter()
    try:
        interp.run(code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
