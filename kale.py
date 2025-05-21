#!/usr/bin/env python3
import curses
import sys
import os
import signal
import pyperclip
import re
import time

os.system('stty -ixon -ignbrk -brkint -icrnl')

# Define color pairs
KEYWORD_COLOR = 1
STRING_COLOR = 2
COMMENT_COLOR = 3
NUMBER_COLOR = 4
OPERATOR_COLOR = 5
FUNCTION_COLOR = 6
#VARIABLE_COLOR = 7 # This broken, make all text red. why use many word when few do job.
PUNCTUATION_COLOR = 8

TOGGLE_ON_COLOR = 9
TOGGLE_OFF_COLOR = 10

HELP_COLOR = 11
# Define keywords for each language CURRENT support for: python, javascript, rust, c, c++, go, java, ruby, html, css, php, typescript, swift, kotlin, scala, perl, lua, r, bash, powershell, sql, json, xml, markdowm, toml, zig
KEYWORDS = {
    'python': ['def', 'class', 'if', 'else', 'elif', 'while', 'for', 'return', 'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'lambda'],
    'javascript': ['function', 'if', 'else', 'while', 'for', 'return', 'import', 'export', 'const', 'let', 'var', 'try', 'catch', 'finally'],
    'rust': ['fn', 'let', 'if', 'else', 'while', 'for', 'return', 'match', 'mod', 'use', 'pub', 'struct', 'enum', 'impl', 'trait'],
    'c': ['int', 'float', 'char', 'if', 'else', 'while', 'for', 'return', 'struct', 'typedef', 'void', 'double', 'switch'],
    'cpp': ['int', 'float', 'char', 'if', 'else', 'while', 'for', 'return', 'class', 'struct', 'public', 'private', 'protected', 'virtual'],
    'go': ['func', 'if', 'else', 'for', 'return', 'import', 'package', 'var', 'const', 'type', 'struct', 'interface', 'go'],
    'java': ['public', 'private', 'protected', 'class', 'if', 'else', 'while', 'for', 'return', 'import', 'static', 'void', 'int'],
    'ruby': ['def', 'class', 'if', 'else', 'elsif', 'while', 'for', 'return', 'require', 'module', 'end', 'begin', 'rescue'],
    'html': ['html', 'head', 'body', 'div', 'span', 'a', 'p', 'h1', 'h2', 'h3', 'img', 'script', 'style', 'table'],
    'css': ['color', 'background', 'font', 'margin', 'padding', 'border', 'display', 'flex', 'grid', 'width', 'height'],
    'php': ['function', 'if', 'else', 'while', 'for', 'return', 'class', 'public', 'private', 'protected', 'echo', 'include'],
    'typescript': ['function', 'if', 'else', 'while', 'for', 'return', 'import', 'export', 'const', 'let', 'interface', 'type'],
    'swift': ['func', 'if', 'else', 'while', 'for', 'return', 'import', 'class', 'struct', 'enum', 'let', 'var', 'guard'],
    'kotlin': ['fun', 'if', 'else', 'while', 'for', 'return', 'import', 'class', 'val', 'var', 'object', 'interface'],
    'scala': ['def', 'if', 'else', 'while', 'for', 'return', 'import', 'class', 'object', 'val', 'var', 'trait'],
    'perl': ['sub', 'if', 'else', 'while', 'for', 'return', 'use', 'my', 'our', 'local', 'print'],
    'lua': ['function', 'if', 'else', 'while', 'for', 'return', 'local', 'end', 'do', 'then'],
    'r': ['function', 'if', 'else', 'while', 'for', 'return', 'library', '<-', 'TRUE', 'FALSE'],
    'bash': ['if', 'else', 'elif', 'fi', 'while', 'for', 'do', 'done', 'case', 'esac', 'function'],
    'powershell': ['function', 'if', 'else', 'while', 'for', 'return', 'param', 'try', 'catch', 'finally'],
    'sql': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'TABLE', 'JOIN', 'ON'],
    'json': ['true', 'false', 'null'],
    'xml': ['xml'],
    'yaml': ['true', 'false', 'null'],
    'markdown': ['#', '##', '###', '*', '**', '-', '```'],
    'toml': ['true', 'false', 'null'],
    'zig': ['fn', 'if', 'else', 'while', 'for', 'return', 'const', 'var', 'pub', 'struct', 'enum', 'comptime', 'export']
}
# Define regular expressions for strings, comments, and numbers
STRING_REGEX = re.compile(r'"[^"]*"|\'[^\']*\'')
COMMENT_REGEX = re.compile(r'#.*|//.*|/\*.*?\*/')
NUMBER_REGEX = re.compile(r'\b\d+\b')
OPERATOR_REGEX = re.compile(r'[+\-*/%=<>!&|]+|==|!=|<=|>=|&&|\|\|')
FUNCTION_REGEX = re.compile(r'\b\w+(?=\s*\()')  # Word followed by ( with optional whitespace
#VARIABLE_REGEX = re.compile(r'\b(?!%s)\w+\b' % '|'.join(re.escape(k) for k in KEYWORDS.get('python', [])))  # Words not in keywords
PUNCTUATION_REGEX = re.compile(r'[(){}\[\],;:.]')
# Editor state
class Kale:
    def __init__(self, filename):
        self.filename = filename
        
        self.lines = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.is_writing = False
        self.is_modified = False
        self.history = []  # Undo stack: list of (lines, cursor_x, cursor_y)
        self.redo_stack = []  # Redo stack
        self.last_edit_time = 0 # groups edits
        self.edit_group_timeout = 0.1#1.0 # seconds grouping consecutive edits
        self.search_query = ""
        self.search_results = []
        self.search_index = -1
        self.is_searching = False
        # Mouse selection state
        self.selection_start = None  # (y, x) tuple or None
        self.selection_end = None    # (y, x) tuple or None
        self.is_selecting = False    # Boolean for selection mode
        self.last_click_time = 0  # Track the time of the last click
        self.click_count = 0  # Track the number of clicks
        self.last_save_time = time.time()
        self.edit_count = 0
        self.show_line_numbers = True  # Toggle for line numbers (default: on)
        self.word_wrap = False  # Toggle for word wrap (default: off)
        self.syntax_highlighting = True  # Default: on
        self.auto_save = True
        self.mouse_support = True  # Toggle for mouse support (default: on)
        self.show_status_bar = True  # Toggle for status bar (default: on)
        self.show_help = False # Toggle for help menu

        self.comment_styles = {
            ".py": "# ",        # Python
            ".js": "// ",       # JavaScript
            ".rs": "// ",       # Rust
            ".c": "// ",        # C (using // for consistency, /* */ optional)
            ".cpp": "// ",      # C++
            ".go": "// ",       # Go
            ".java": "// ",     # Java
            ".rb": "# ",        # Ruby
            ".html": "<!-- ",   # HTML
            ".css": "/* ",      # CSS
            ".php": "// ",      # PHP (also supports #, but // matches JS/TS)
            ".ts": "// ",       # TypeScript
            ".swift": "// ",    # Swift
            ".kt": "// ",       # Kotlin
            ".scala": "// ",    # Scala
            ".pl": "# ",        # Perl
            ".lua": "-- ",      # Lua
            ".r": "# ",         # R
            ".sh": "# ",        # Bash
            ".ps1": "# ",       # PowerShell
            ".sql": "-- ",      # SQL
            ".json": "// ",     # JSON (unofficial, but common in editors)
            ".xml": "<!-- ",    # XML
            ".md": "<!-- ",     # Markdown (HTML-style comments)
            ".toml": "# ",      # TOML
            ".zig": "// "       # Zig
        }
        self.comment_end_styles = {
            ".html": " -->",    # HTML
            ".css": " */",      # CSS
            ".xml": " -->",     # XML
            ".md": " -->"       # Markdown
        }
        if filename:
            try:
                with open(filename, 'r', newline='', encoding='utf-8', errors='replace') as f:
                    raw_lines = f.readlines()
                    self.lines = [''.join(c for c in line if ord(c) >= 32 or c == '\n').rstrip('\r\n') for line in raw_lines]
            except FileNotFoundError:
                self.lines = [""]
        else:
            self.lines = [""]
        if filename and os.path.exists(f"{filename}.kale_pos"):
            with open(f"{filename}.kale_pos", 'r') as pos_file:
                y, x = map(int, pos_file.read().split(','))
                self.cursor_y = max(0, min(y, len(self.lines) - 1))
                self.cursor_x = max(0, min(x, len(self.lines[self.cursor_y])))


    def toggle_comment(self, stdscr, max_y):
        """Toggle comments on selected lines based on file type."""
        if not (self.selection_start and self.selection_end):
            stdscr.addstr(max_y - 2, 0, "No selection to comment", curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.5)
            return
        
        self.save_history("comment")
        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x

        # Detect comment style based on file extension
        ext = self.filename[self.filename.rfind("."):] if "." in self.filename else ""
        comment_prefix = self.comment_styles.get(ext, "# ")  # Default to # if unknown
        comment_suffix = self.comment_end_styles.get(ext, "")  # End marker if applicable

        # Toggle comments: add if not present, remove if already commented
        all_commented = True
        for i in range(start_y, end_y + 1):
            line = self.lines[i]
            if not line.lstrip().startswith(comment_prefix):
                all_commented = False
                break

        if all_commented:
            # Uncomment
            for i in range(start_y, end_y + 1):
                line = self.lines[i]
                if line.lstrip().startswith(comment_prefix):
                    stripped = line.lstrip()
                    indent = line[:len(line) - len(stripped)]
                    self.lines[i] = indent + stripped[len(comment_prefix):].rstrip(comment_suffix)
        else:
            # Comment
            for i in range(start_y, end_y + 1):
                line = self.lines[i]
                if line.strip():  # Only comment non-empty lines
                    self.lines[i] = comment_prefix + line + (comment_suffix if i == end_y else "")
                elif i == start_y or i == end_y:  # Empty start/end lines get comment
                    self.lines[i] = comment_prefix + (comment_suffix if i == end_y else "")

        self.is_modified = True
        stdscr.addstr(max_y - 2, 0, "Toggled comments", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(0.3)
        self.selection_start = (start_y, 0)  # Reset selection to full lines
        self.selection_end = (end_y, len(self.lines[end_y]))

    def uncomment_selection(self, stdscr, max_y):
        """Remove comments from selected lines based on file type."""
        if not (self.selection_start and self.selection_end):
            stdscr.addstr(max_y - 2, 0, "No selection to uncomment", curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.5)
            return
        
        self.save_history("uncomment")
        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x

        # Detect comment style based on file extension
        ext = self.filename[self.filename.rfind("."):] if "." in self.filename else ""
        comment_prefix = self.comment_styles.get(ext, "# ")  # Default to # if unknown
        comment_suffix = self.comment_end_styles.get(ext, "")  # End marker if applicable

        # Uncomment lines
        modified = False
        for i in range(start_y, end_y + 1):
            line = self.lines[i]
            stripped = line.lstrip()
            if stripped.startswith(comment_prefix):
                indent = line[:len(line) - len(stripped)]
                uncommented = stripped[len(comment_prefix):].rstrip(comment_suffix)
                self.lines[i] = indent + uncommented
                modified = True

        if modified:
            self.is_modified = True
            stdscr.addstr(max_y - 2, 0, "Uncommented selection", curses.A_BOLD)
        else:
            stdscr.addstr(max_y - 2, 0, "No comments removed", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(0.3)
        self.selection_start = (start_y, 0)  # Reset selection to full lines
        self.selection_end = (end_y, len(self.lines[end_y]))


    def should_increase_indentation(self, line):
        """Check if the current line should trigger an increase in indentation."""
        language = self.get_language()
        if language == 'python':
            if line.rstrip().endswith(':'):
                return True
        elif language == 'javascript':
            if line.rstrip().endswith(('{', '[', '(')):
                return True
        elif language == 'rust':
            if line.rstrip().endswith('{'):
                return True
        elif language == 'c':
            if line.rstrip().endswith('{'):
                return True
        return False

    def should_decrease_indentation(self, line):
        """Check if the current line should trigger a decrease in indentation."""
        language = self.get_language()
        if language == 'python':
            keywords = ['return', 'break', 'continue', 'pass']
            for keyword in keywords:
                if line.rstrip() == keyword:
                    return True
        elif language == 'javascript':
            if line.rstrip().endswith(('}', ']', ')')):
                return True
        elif language == 'rust':
            if line.rstrip().endswith('}'):
                return True
        elif language == 'c':
            if line.rstrip().endswith('}'):
                return True
        return False

    def save_file(self, stdscr):
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.lines))
        with open(f"{self.filename}.kale_pos", 'w') as pos_file:
            pos_file.write(f"{self.cursor_y},{self.cursor_x}")
        self.is_modified = False
        stdscr.addstr(0, 0, "Saved!", curses.A_BOLD)


    def save_history(self, action="edit"):
        """Save the current state to history."""
        MAX_HISTORY_SIZE = 100
        current_time = time.time()
        state = (
            self.lines[:], 
            self.cursor_x, 
            self.cursor_y,
            self.selection_start, 
            self.selection_end, 
            self.is_selecting,
            action  # Add action type
        )
        
        # Group edits if within timeout and same action
        if (self.history and 
            current_time - self.last_edit_time < self.edit_group_timeout and 
            self.history[-1][-1] == action):  # Check action type (last element)
            self.history[-1] = state  # Overwrite last edit
        else:
            if len(self.history) >= MAX_HISTORY_SIZE:
                self.history.pop(0)
            self.history.append(state)
            self.redo_stack = []  # Clear redo stack on new change
        self.last_edit_time = current_time

    def undo(self, stdscr=None, max_y=None):
        """Undo the last change."""
        if not self.history:
            if stdscr and max_y:
                stdscr.addstr(max_y - 2, 0, "Nothing to undo", curses.A_BOLD)
                stdscr.refresh()
                time.sleep(0.5)
            return
        current_state = (
            self.lines[:], 
            self.cursor_x, 
            self.cursor_y,
            self.selection_start, 
            self.selection_end, 
            self.is_selecting,
            "current"  # Placeholder action
        )
        self.redo_stack.append(current_state)
        lines, x, y, sel_start, sel_end, is_sel, action = self.history.pop()
        self.lines = lines[:]
        self.cursor_x = x
        self.cursor_y = y
        self.selection_start = sel_start
        self.selection_end = sel_end
        self.is_selecting = is_sel
        self.is_modified = True
        if stdscr and max_y:
            stdscr.addstr(max_y - 2, 0, f"Undone {action}", curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.3)

    def redo(self, stdscr=None, max_y=None):
        """Redo the last undone change."""
        if not self.redo_stack:
            if stdscr and max_y:
                stdscr.addstr(max_y - 2, 0, "Nothing to redo", curses.A_BOLD)
                stdscr.refresh()
                time.sleep(0.5)
            return
        current_state = (
            self.lines[:], 
            self.cursor_x, 
            self.cursor_y,
            self.selection_start, 
            self.selection_end, 
            self.is_selecting,
            "current"  # Placeholder action
        )
        self.history.append(current_state)
        lines, x, y, sel_start, sel_end, is_sel, action = self.redo_stack.pop()
        self.lines = lines[:]
        self.cursor_x = x
        self.cursor_y = y
        self.selection_start = sel_start
        self.selection_end = sel_end
        self.is_selecting = is_sel
        self.is_modified = True
        if stdscr and max_y:
            stdscr.addstr(max_y - 2, 0, f"Redone {action}", curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.3)

    def search(self, query):
        self.search_results = []
        if query:
            for y, line in enumerate(self.lines):
                x = 0
                while x != -1:
                    x = line.find(query, x)
                    if x != -1:
                        self.search_results.append((y, x))
                        x += 1
                    else:
                        break

    def find_previous_word(self):
        """Move the cursor to the start of the previous word."""
        line = self.lines[self.cursor_y]
        if self.cursor_x == 0:
            if self.cursor_y == 0:
                return
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])
            line = self.lines[self.cursor_y]
        while self.cursor_x > 0 and line[self.cursor_x - 1].isalnum():
            self.cursor_x -= 1
        while self.cursor_x > 0 and not line[self.cursor_x - 1].isalnum():
            self.cursor_x -= 1

    def find_next_word(self):
        """Move the cursor to the start of the next word."""
        line = self.lines[self.cursor_y]
        if self.cursor_x >= len(line):
            if self.cursor_y == len(self.lines) - 1:
                return
            self.cursor_y += 1
            self.cursor_x = 0
            line = self.lines[self.cursor_y]
        while self.cursor_x < len(line) and line[self.cursor_x].isalnum():
            self.cursor_x += 1
        while self.cursor_x < len(line) and not line[self.cursor_x].isalnum():
            self.cursor_x += 1

    def get_language(self):
        ext = os.path.splitext(self.filename)[1].lower()
        return {
            '.py': 'python',
            '.js': 'javascript',
            '.rs': 'rust',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.go': 'go',
            '.java': 'java',
            '.rb': 'ruby',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.php': 'php',
            '.ts': 'typescript',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.pl': 'perl',
            '.lua': 'lua',
            '.r': 'r',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.toml': 'toml',
            '.zig': 'zig'
        }.get(ext, 'text')  # Default to 'text' (no highlighting) if unknown


    def highlight_tokens(self, line, language):
        if not line or not self.syntax_highlighting:
            return [(line, curses.color_pair(0))]
        matches = []
        
        # Comments (highest precedence)
        for match in COMMENT_REGEX.finditer(line):
            matches.append((match.span(), COMMENT_COLOR, "comment"))
        
        # Strings (next precedence)
        for match in STRING_REGEX.finditer(line):
            matches.append((match.span(), STRING_COLOR, "string"))
        
        # Keywords
        for keyword in KEYWORDS.get(language, []):
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', line):
                matches.append((match.span(), KEYWORD_COLOR, "keyword"))
        
        # Numbers
        for match in NUMBER_REGEX.finditer(line):
            matches.append((match.span(), NUMBER_COLOR, "number"))
        
        # Operators
        for match in OPERATOR_REGEX.finditer(line):
            matches.append((match.span(), OPERATOR_COLOR, "operator"))
        
        # Functions (word followed by '(')
        for match in FUNCTION_REGEX.finditer(line):
            if match.group() not in KEYWORDS.get(language, []):  # Exclude keywords
                matches.append((match.span(), FUNCTION_COLOR, "function"))
        
        # Variables (words not keywords or functions)
       # keywords = set(KEYWORDS.get(language, []))
       # for match in re.finditer(r'\b\w+\b', line):
       #     word = match.group()
       #     if (word not in keywords and 
       #         not re.match(r'\b' + re.escape(word) + r'\s*\(', line[match.start():])):
       #         matches.append((match.span(), VARIABLE_COLOR, "variable"))
        
        # Punctuation
        for match in PUNCTUATION_REGEX.finditer(line):
            matches.append((match.span(), PUNCTUATION_COLOR, "punctuation"))
        
        # Sort and merge overlapping matches
        matches.sort(key=lambda x: (x[0][0], -x[0][1] + x[0][0], x[2]))
        highlighted_line = []
        pos = 0
        used_spans = set()
        for (start, end), color, token_type in matches:
            if any(start <= p < end for p in used_spans):
                continue
            if start > pos:
                highlighted_line.append((line[pos:start], curses.color_pair(0)))
            attr = curses.color_pair(color)
            if token_type in ("keyword", "string", "number", "operator", "function"):
                attr |= curses.A_BOLD  # Bold for these types
            highlighted_line.append((line[start:end], attr))
            used_spans.update(range(start, end))
            pos = max(pos, end)
        if pos < len(line):
            highlighted_line.append((line[pos:], curses.color_pair(0)))
        return highlighted_line


    def get_selected_text(self):
        """Return the text within the current selection range."""
        if not self.selection_start or not self.selection_end:
            return ""
        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
        selected_text = []
        for y in range(start_y, end_y + 1):
            if y == start_y and y == end_y:
                selected_text.append(self.lines[y][start_x:end_x])
            elif y == start_y:
                selected_text.append(self.lines[y][start_x:])
            elif y == end_y:
                selected_text.append(self.lines[y][:end_x])
            else:
                selected_text.append(self.lines[y])
        return "\n".join(selected_text)

    def run(self, stdscr):
        # Initialize colors
        curses.start_color()
        curses.init_pair(KEYWORD_COLOR, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Keywords: Bright Magenta, bold
        curses.init_pair(STRING_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)     # Strings: Bright Green, bold
        curses.init_pair(COMMENT_COLOR, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Comments: Bright Cyan, normal
        curses.init_pair(NUMBER_COLOR, curses.COLOR_YELLOW, curses.COLOR_BLACK)    # Numbers: Bright Yellow, bold
        curses.init_pair(OPERATOR_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Operators: Bright White, bold
        curses.init_pair(FUNCTION_COLOR, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Functions: Bright Blue, bold
        #curses.init_pair(VARIABLE_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)     # Variables: Bright Red, normal
        curses.init_pair(PUNCTUATION_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK) # Punctuation: Bright White, normal
        
        curses.init_pair(TOGGLE_ON_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK) # Status bar toggles ON indicator
        curses.init_pair(TOGGLE_OFF_COLOR, curses.COLOR_RED, curses.COLOR_BLACK) # status bar toggle OFF indicator
        curses.init_pair(HELP_COLOR,curses.COLOR_YELLOW, curses.COLOR_BLACK) # HELP ME button in status bar <3

        curses.raw()
        stdscr.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        stdscr.timeout(300)  # Keep original timeout

        last_max_y = 0  # Track window height for resize detection
        help_x_start = None
        # Store state before loading help
        self.previous_state = None  # {lines, filename, cursor_y, cursor_x, scroll_y, scroll_x, is_modified}
        MIN_WIDTH = 40  # Minimum terminal width
        MIN_HEIGHT = 5  # Minimum terminal height
        
        while True:
            
            self.edit_count += 1
            current_time = time.time()
            if self.auto_save and ((current_time - self.last_save_time > 300) or (self.edit_count > 100)):
                self.save_file(stdscr)
                self.last_save_time = current_time
                self.edit_count = 0

            max_y, max_x = stdscr.getmaxyx()
            max_line_number_width = len(str(len(self.lines))) if self.show_line_numbers else 0


            if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:
                stdscr.clear()
                error_msg = f"Terminal too small ({max_x}x{max_y}). Min: {MIN_WIDTH}x{MIN_HEIGHT}. Resize and press any key."
                stdscr.addstr(0, 0, error_msg[:max_x - 1])  # Clip to fit tiny screens
                stdscr.refresh()
                stdscr.getch()
                continue

            if max_y != last_max_y:
                stdscr.clear()
                last_max_y = max_y
            else:
                stdscr.erase()
            # Only clear on resize or initial run
            if max_y != last_max_y:
                stdscr.clear()
                last_max_y = max_y
            else:
                stdscr.erase()  # Mark for update without immediate wipe

            if not self.lines:
                self.lines.append("")

            if self.show_help:
                help_text = [
                    "Keybindings:",
                    "Space: WRITE mode  Ctrl+S: Save  Ctrl+Q: Quit",
                    "wasd: Move  jj: Jump  tn: Line nums  tm: Wrap",
                    "ts: Syntax  ta: Auto-save  to: Mouse  tb: Status",
                    "Press Esc to exit this help",
                ]
                for i, line in enumerate(help_text[:max_y]):
                    stdscr.addstr(i, 0, line[:max_x - 1])
                stdscr.refresh()
                key = stdscr.getch()
                if key == 27:  # Esc to exit help
                    self.show_help = False
                continue

            # Bounds checking
            render_height = max_y - 1 if self.show_status_bar else max_y
            self.scroll_y = max(0, min(self.scroll_y, len(self.lines) - render_height))
            self.scroll_x = max(0, min(self.scroll_x, max(len(line) for line in self.lines) - (max_x - max_line_number_width - 1)))
            self.cursor_y = max(0, min(self.cursor_y, len(self.lines) - 1))
            self.cursor_x = max(0, min(self.cursor_x, len(self.lines[self.cursor_y])))

            # Adjust scroll to keep cursor in view
            if self.cursor_y < self.scroll_y:
                self.scroll_y = self.cursor_y
            elif self.cursor_y >= self.scroll_y + render_height:
                self.scroll_y = self.cursor_y - (render_height - 1)
            if self.cursor_x < self.scroll_x:
                self.scroll_x = self.cursor_x
            elif self.cursor_x >= self.scroll_x + (max_x - max_line_number_width - 1):
                self.scroll_x = self.cursor_x - (max_x - max_line_number_width - 2)

            # Render lines
            for i in range(render_height):
                line_index = self.scroll_y + i
                if line_index < len(self.lines):
                    line = self.lines[line_index]
                    if self.show_line_numbers:
                        line_number = f"{line_index + 1:>{max_line_number_width}}:"
                        stdscr.addstr(i, 0, line_number, curses.color_pair(0))
                    if self.word_wrap:
                        visible_width = max_x - max_line_number_width - 1
                        wrapped_lines = [line[j:j + visible_width] for j in range(0, len(line), visible_width)]
                        for j, wrapped_line in enumerate(wrapped_lines):
                            if i + j < render_height:
                                if self.syntax_highlighting:
                                    highlighted_line = self.highlight_tokens(wrapped_line, self.get_language())
                                else:
                                    highlighted_line = [(wrapped_line, curses.color_pair(0))]
                                x_offset = max_line_number_width + 1 if self.show_line_numbers else 0
                                for text, color in highlighted_line:
                                    if x_offset < max_x:
                                        safe_length = max(0, max_x - x_offset)
                                        safe_text = text[:safe_length]
                                        stdscr.addstr(i + j, x_offset, safe_text, color)
                                        x_offset += len(safe_text)
                    else:
                        visible_start = self.scroll_x
                        visible_end = min(len(line), visible_start + (max_x - max_line_number_width - 1))
                        visible_line = line[visible_start:visible_end]
                        if self.syntax_highlighting:
                            highlighted_line = self.highlight_tokens(visible_line, self.get_language())
                        else:
                            highlighted_line = [(visible_line, curses.color_pair(0))]
                        x_offset = max_line_number_width + 1 if self.show_line_numbers else 0
                        for text, color in highlighted_line:
                            if x_offset < max_x:
                                safe_length = max(0, max_x - x_offset)
                                safe_text = text[:safe_length]
                                stdscr.addstr(i, x_offset, safe_text, color)
                                x_offset += len(safe_text)
            if self.show_status_bar:
                # Recheck max_x right before status bar to catch mid-loop resizes
                max_y, max_x = stdscr.getmaxyx()
                if max_y < MIN_HEIGHT or max_x < MIN_WIDTH:  # Local MIN_HEIGHT, MIN_WIDTH
                    continue

                word_count = sum(len(line.split()) for line in self.lines)
                mode = "WRITE" if self.is_writing else ("SELECTING" if self.selection_start else "COMMAND")
                modified = "*" if self.is_modified else ""
                file_size = sum(len(line.encode('utf-8')) for line in self.lines) + len(self.lines) - 1
                file_size_kb = f"{file_size / 1024:.1f}KB" if file_size > 1024 else f"{file_size}B"
                percent = f"{(self.cursor_y + 1) / len(self.lines) * 100:.0f}%" if self.lines else "0%"
                core_status = f"{self.filename}{modified} - ({self.cursor_y + 1},{self.cursor_x + 1})"
                stdscr.addstr(max_y - 1, 0, core_status[:max_x - 1].ljust(max_x - 1))
                x_offset = len(core_status)

                if x_offset + 10 < max_x:
                    chunk = f" {percent} {file_size_kb}"[:max_x - x_offset - 1]
                    stdscr.addstr(max_y - 1, x_offset, chunk)
                    x_offset += len(chunk)
                if x_offset + 15 < max_x:
                    chunk = f" MODE: {mode} Words: {word_count}"[:max_x - x_offset - 1]
                    stdscr.addstr(max_y - 1, x_offset, chunk)
                    x_offset += len(chunk)
                if x_offset + 26 < max_x:
                    ln_color = curses.color_pair(TOGGLE_ON_COLOR) | curses.A_BOLD if self.show_line_numbers else curses.color_pair(TOGGLE_OFF_COLOR)
                    stdscr.addstr(max_y - 1, x_offset, " LN"[:max_x - x_offset - 1], ln_color)
                    x_offset += 3
                    if x_offset + 16 < max_x:
                        ww_color = curses.color_pair(TOGGLE_ON_COLOR) | curses.A_BOLD if self.word_wrap else curses.color_pair(TOGGLE_OFF_COLOR)
                        stdscr.addstr(max_y - 1, x_offset, " WW"[:max_x - x_offset - 1], ww_color)
                        x_offset += 3
                    if x_offset + 13 < max_x:
                        as_color = curses.color_pair(TOGGLE_ON_COLOR) | curses.A_BOLD if self.auto_save else curses.color_pair(TOGGLE_OFF_COLOR)
                        stdscr.addstr(max_y - 1, x_offset, " AS"[:max_x - x_offset - 1], as_color)
                        x_offset += 3
                    if x_offset + 10 < max_x:
                        syn_color = curses.color_pair(TOGGLE_ON_COLOR) | curses.A_BOLD if self.syntax_highlighting else curses.color_pair(TOGGLE_OFF_COLOR)
                        stdscr.addstr(max_y - 1, x_offset, " SYN"[:max_x - x_offset - 1], syn_color)
                        x_offset += 4
                    if x_offset + 6 < max_x:
                        ms_color = curses.color_pair(TOGGLE_ON_COLOR) | curses.A_BOLD if self.mouse_support else curses.color_pair(TOGGLE_OFF_COLOR)
                        stdscr.addstr(max_y - 1, x_offset, " MS"[:max_x - x_offset - 1], ms_color)
                        x_offset += 3
                    if x_offset + 10 < max_x:
                        stdscr.addstr(max_y - 1, x_offset, " HELP : th"[:max_x - x_offset - 1], curses.color_pair(HELP_COLOR) | curses.A_BOLD)
                    
            ###
            # Search display
            if self.is_searching:
                self.is_writing = False
                stdscr.addstr(max_y - 2, 0, f"Search: {self.search_query}", curses.A_BOLD)
                if self.search_results:
                    status = f"Search: {self.search_query} - Match {self.search_index + 1}/{len(self.search_results)}"
                    stdscr.addstr(max_y - 1, 0, status[:max_x - 1], curses.A_BOLD)

            # Highlight search results
            if self.search_results:
                for y, x in self.search_results:
                    if self.scroll_y <= y < self.scroll_y + (max_y - 2):
                        visible_text = self.lines[y][self.scroll_x:self.scroll_x + max_x - max_line_number_width - 1]
                        pos = visible_text.find(self.search_query)
                        if pos != -1:
                            attr = curses.A_REVERSE if (y, x) == self.search_results[self.search_index] else curses.A_UNDERLINE
                            stdscr.addstr(y - self.scroll_y, pos + max_line_number_width + 1, self.search_query, attr)

            # Highlight selection
            if self.selection_start and self.selection_end:
                start_y, start_x = self.selection_start
                end_y, end_x = self.selection_end
                if start_y > end_y or (start_y == end_y and start_x > end_x):
                    start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                for y in range(start_y, end_y + 1):
                    if y < self.scroll_y or y >= self.scroll_y + (max_y - 1):
                        continue
                    line = self.lines[y]
                    line_start = 0
                    line_end = len(line)
                    if y == start_y:
                        line_start = start_x
                    if y == end_y:
                        line_end = end_x
                    visible_start = max(0, line_start - self.scroll_x)
                    visible_end = min(max_x - max_line_number_width - 1, line_end - self.scroll_x)
                    if visible_start < visible_end:
                        stdscr.addstr(y - self.scroll_y, visible_start + max_line_number_width + 1,
                                      line[line_start:line_end][:visible_end - visible_start], curses.A_REVERSE)

            # Position cursor
            cursor_y_in_text = self.cursor_y - self.scroll_y
            cursor_x_in_text = self.cursor_x - self.scroll_x
            x_offset = max_line_number_width + 1 if self.show_line_numbers else 0
            if 0 <= cursor_y_in_text < max_y - 1 and 0 <= cursor_x_in_text + x_offset < max_x:
                stdscr.move(cursor_y_in_text, cursor_x_in_text + x_offset)
                
            stdscr.refresh()  # Single refresh at the end

            key = stdscr.getch()

            # Close README.txt with Esc
            if key == 27 and self.previous_state is not None:  # Esc key
                self.lines = self.previous_state["lines"]
                self.filename = self.previous_state["filename"]
                self.cursor_y = self.previous_state["cursor_y"]
                self.cursor_x = self.previous_state["cursor_x"]
                self.scroll_y = self.previous_state["scroll_y"]
                self.scroll_x = self.previous_state["scroll_x"]
                self.is_modified = self.previous_state["is_modified"]
                self.previous_state = None
                
            if key == curses.KEY_MOUSE and self.mouse_support:
                try:
                    _, mx, my, _, mouse_state = curses.getmouse()
                except curses.error:
                    continue

                # Check for "th" click first (status bar help)
                if my == max_y - 1 and help_x_start is not None and help_x_start <= mx < help_x_start + 3:
                    if mouse_state & curses.BUTTON1_PRESSED:
                        # Save current state before loading help
                        self.previous_state = {
                            "lines": self.lines.copy(),
                            "filename": self.filename,
                            "cursor_y": self.cursor_y,
                            "cursor_x": self.cursor_x,
                            "scroll_y": self.scroll_y,
                            "scroll_x": self.scroll_x,
                            "is_modified": self.is_modified
                        }
                        # Load README.txt
                        try:
                            with open("README.txt", "r") as f:
                                self.lines = f.read().splitlines()
                            self.filename = "README.txt"
                            self.is_modified = False
                        except FileNotFoundError:
                            self.lines = ["README.txt not found!"]
                            self.filename = "README.txt"
                            self.is_modified = True
                        self.cursor_y = 0
                        self.cursor_x = 0
                        self.scroll_y = 0
                        self.scroll_x = 0
                    continue  # Skip other mouse actions if "th" is clicked

                # General mouse handling (scrolling, clicking, selecting)
                clicked_y = my + self.scroll_y
                clicked_x = mx - (max_line_number_width + 1) + self.scroll_x
                clicked_y = max(0, min(clicked_y, len(self.lines) - 1))
                clicked_x = max(0, min(clicked_x, len(self.lines[clicked_y])))

                if mouse_state & curses.BUTTON4_PRESSED:  # Scroll up
                    self.scroll_y = max(0, self.scroll_y - 3)
                    self.cursor_y = max(0, self.cursor_y - 3)
                elif mouse_state & curses.BUTTON5_PRESSED:  # Scroll down
                    self.scroll_y = min(max(0, len(self.lines) - (max_y - 1)), self.scroll_y + 3)
                    self.cursor_y = min(len(self.lines) - 1, self.cursor_y + 3)
                elif mouse_state & curses.BUTTON1_PRESSED and not self.is_selecting:
                    current_time = time.time()
                    time_since_last_click = current_time - self.last_click_time
                    if time_since_last_click < 0.3:  # Double-click
                        line = self.lines[clicked_y]
                        start_x = clicked_x
                        end_x = clicked_x
                        while start_x > 0 and line[start_x - 1].isalnum():
                            start_x -= 1
                        while end_x < len(line) and line[end_x].isalnum():
                            end_x += 1
                        self.selection_start = (clicked_y, start_x)
                        self.selection_end = (clicked_y, end_x)
                        self.cursor_y = clicked_y
                        self.cursor_x = end_x
                        self.is_selecting = False
                        self.click_count += 1
                    else:  # Single click
                        self.cursor_y = clicked_y
                        self.cursor_x = clicked_x
                        self.selection_start = (clicked_y, clicked_x)
                        self.selection_end = None
                        self.is_selecting = True
                        self.click_count = 1
                    self.last_click_time = current_time
                elif mouse_state & curses.BUTTON1_PRESSED and self.is_selecting:
                    self.selection_end = (clicked_y, clicked_x)
                elif mouse_state & curses.BUTTON1_RELEASED and self.is_selecting:
                    self.selection_end = (clicked_y, clicked_x)
                    self.is_selecting = False
                    start_y, start_x = self.selection_start
                    end_y, end_x = self.selection_end
                    if start_y < end_y or (start_y == end_y and start_x <= end_x):  # Top-down or left-to-right
                        self.cursor_y = end_y
                        self.cursor_x = end_x
                    else:  # Bottom-up or right-to-left
                        self.cursor_y = start_y
                        self.cursor_x = start_x

            # Search mode
            elif self.is_searching:
                self.is_writing = False
                if key == 27:  # Esc
                    self.is_searching = False
                    self.search_query = ""
                    self.search_results = []
                    self.search_index = -1
                elif key == 10:  # Enter
                    self.save_history()
                    current_line = self.lines[self.cursor_y]
                    self.is_searching = False
                    self.search_query = ""
                    self.search_results = []
                    self.search_index = -1
                elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                    if self.search_query:  # Only if there's something to delete
                        self.search_query = self.search_query[:-1]
                        if self.search_query:  # Update search if query isn't empty
                            self.search(self.search_query)
                            self.search_index = 0 if self.search_results else -1
                        else:  # Clear results if query is empty
                            self.search_results = []
                            self.search_index = -1
                elif 32 <= key <= 126:  # Printable characters
                    self.search_query += chr(key)
                    self.search(self.search_query)
                    self.search_index = 0 if self.search_results else -1
                elif key == curses.KEY_DOWN:
                    if self.search_results:
                        self.search_index = (self.search_index + 1) % len(self.search_results)
                        line, col = self.search_results[self.search_index]
                        self.cursor_y = line
                        self.cursor_x = col
                elif key == curses.KEY_UP:
                    if self.search_results:
                        self.search_index = (self.search_index - 1) % len(self.search_results)
                        line, col = self.search_results[self.search_index]
                        self.cursor_y = line
                        self.cursor_x = col
                continue


            # COMMAND mode
            elif not self.is_writing:
                if key in (ord('w'), ord('W')):
                    self.cursor_y = max(0, self.cursor_y - 1)
                elif key in (ord('s'), ord('S')):
                    self.cursor_y = min(len(self.lines) - 1, self.cursor_y + 1)
                elif key in (ord('a'), ord('A')):
                    self.cursor_x = max(0, self.cursor_x - 1)
                elif key in (ord('d'), ord('D')):
                    self.cursor_x = min(len(self.lines[self.cursor_y]), self.cursor_x + 1)
########### HOTKEY JUMP TO FUNCTIONS ###############
                elif key == ord('j'):
                    stdscr.timeout(-1)  # Wait indefinitely for the next key
                    next_key = stdscr.getch()
                    stdscr.timeout(300)  # Restore original timeout #100
                    if next_key == ord('q'):  # Top of file
                        self.cursor_y = 0
                        self.cursor_x = 0
                        self.scroll_y = 0
                        self.scroll_x = 0
                    elif next_key == ord('e'):  # Bottom of file
                        self.cursor_y = len(self.lines) - 1
                        self.cursor_x = len(self.lines[self.cursor_y])
                        self.scroll_y = max(0, len(self.lines) - (max_y - 1))
                        if self.cursor_y < self.scroll_y:
                            self.scroll_y = self.cursor_y
                    elif next_key == ord('w'):  # Up one page
                        page_size = max_y - 2
                        self.cursor_y = max(0, self.cursor_y - page_size)
                        self.scroll_y = max(0, self.scroll_y - page_size)
                        if self.cursor_y < self.scroll_y:
                            self.scroll_y = self.cursor_y
                    elif next_key == ord('s'):  # Down one page
                        page_size = max_y - 2
                        self.cursor_y = min(len(self.lines) - 1, self.cursor_y + page_size)
                        self.scroll_y = min(max(0, len(self.lines) - (max_y - 1)), self.scroll_y + page_size)
                        if self.cursor_y >= self.scroll_y + (max_y - 1):
                            self.scroll_y = self.cursor_y - (max_y - 2)
                    elif next_key == ord('a'):  # Start of line
                        self.cursor_x = 0
                        self.scroll_x = 0
                    elif next_key == ord('d'):  # End of line
                        self.cursor_x = len(self.lines[self.cursor_y])
                        if self.cursor_x >= self.scroll_x + (max_x - max_line_number_width - 1):
                            self.scroll_x = self.cursor_x - (max_x - max_line_number_width - 2)
                    elif next_key == ord('k'):  # Half page up
                        half_page = (max_y - 2) // 2
                        self.cursor_y = max(0, self.cursor_y - half_page)
                        self.scroll_y = max(0, self.scroll_y - half_page)
                        if self.cursor_y < self.scroll_y:
                            self.scroll_y = self.cursor_y
                    elif next_key == ord('l'):  # Half page down
                        half_page = (max_y - 2) // 2
                        self.cursor_y = min(len(self.lines) - 1, self.cursor_y + half_page)
                        self.scroll_y = min(max(0, len(self.lines) - (max_y - 1)), self.scroll_y + half_page)
                        if self.cursor_y >= self.scroll_y + (max_y - 1):
                            self.scroll_y = self.cursor_y - (max_y - 2)
                    elif next_key == ord('j'):  # Jump to line
                        line_number = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Jump to line: {line_number}", curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if line_number:
                                    try:
                                        target_line = int(line_number) - 1  # Convert to 0-indexed
                                        if 0 <= target_line < len(self.lines):
                                            self.cursor_y = target_line
                                            self.cursor_x = 0
                                            self.scroll_y = max(0, self.cursor_y - (max_y // 2))  # Center line in view
                                            if self.cursor_y < self.scroll_y:
                                                self.scroll_y = self.cursor_y
                                        else:
                                            stdscr.addstr(max_y - 2, 0, f"Line {line_number} out of range (1-{len(self.lines)})")
                                            stdscr.refresh()
                                            time.sleep(0.5)
                                    except ValueError:
                                        stdscr.addstr(max_y - 2, 0, "Invalid number")
                                        stdscr.refresh()
                                        time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                line_number = line_number[:-1]
                            elif 48 <= key <= 57:  # Digits 0-9
                                line_number += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    else:
                        stdscr.addstr(max_y - 2, 0, f"Unknown command: j + {chr(next_key) if 32 <= next_key <= 126 else next_key}")
                        stdscr.refresh()
                        time.sleep(0.5)  # Show feedback briefly
########### HOTKEY TOGGLE FUNCTIONS ###############

                elif key == ord('t'):  # Toggle commands
                    stdscr.timeout(-1)  # Wait for next key
                    next_key = stdscr.getch()
                    stdscr.timeout(300)  # Restore timeout
                    if next_key == ord('n'):  # Toggle line numbers
                        self.show_line_numbers = not self.show_line_numbers
                        stdscr.addstr(max_y - 2, 0, f"Line numbers: {'on' if self.show_line_numbers else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('m'):  # Toggle word wrap
                        self.word_wrap = not self.word_wrap
                        stdscr.addstr(max_y - 2, 0, f"Word wrap: {'on' if self.word_wrap else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('s'):  # Toggle syntax highlighting
                        self.syntax_highlighting = not self.syntax_highlighting
                        stdscr.addstr(max_y - 2, 0, f"Syntax highlighting: {'on' if self.syntax_highlighting else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('a'):  # Toggle auto-save
                        self.auto_save = not self.auto_save
                        stdscr.addstr(max_y - 2, 0, f"Auto-save: {'on' if self.auto_save else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('o'):  # Toggle mouse support
                        self.mouse_support = not self.mouse_support
                        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION if self.mouse_support else 0)
                        stdscr.addstr(max_y - 2, 0, f"Mouse support: {'on' if self.mouse_support else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('b'):  # Toggle status bar
                        self.show_status_bar = not self.show_status_bar
                        stdscr.addstr(max_y - 2, 0, f"Status bar: {'on' if self.show_status_bar else 'off'}", curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(0.5)
                    elif next_key == ord('h'):  # Toggle help screen
                        self.show_help = not self.show_help
                    elif next_key == ord('c'):  # Toggle comment
                            self.toggle_comment(stdscr, max_y)
                    elif next_key == ord('u'):  # Toggle uncomment
                                    self.uncomment_selection(stdscr, max_y)
                    elif next_key == ord('p'):  # Toggle command palette
                        command = ""
                        available_commands = [
                            "save", "quit", "jump", "replace next", "replace all",
                            "toggle line numbers", "toggle word wrap", "toggle syntax highlighting"
                        ]
                        while True:
                            stdscr.clear()  # Clear screen for clean palette display
                            stdscr.addstr(0, 0, "Command Palette", curses.A_BOLD)
                            stdscr.addstr(1, 0, "Available: " + ", ".join(available_commands)[:max_x - 1])
                            stdscr.addstr(max_y - 2, 0, f"Command: {command}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                stdscr.clear()
                                if command == "save":
                                    self.save_file(stdscr)
                                    stdscr.addstr(max_y - 2, 0, "File saved", curses.A_BOLD)
                                elif command == "quit":
                                    stdscr.addstr(max_y - 2, 0, "Quitting", curses.A_BOLD)
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                    return  # Exit the entire run method
                                elif command == "jump":
                                    line_number = ""
                                    while True:
                                        stdscr.addstr(max_y - 2, 0, f"Jump to line: {line_number}"[:max_x - 1], curses.A_BOLD)
                                        stdscr.refresh()
                                        key = stdscr.getch()
                                        if key == 10:
                                            if line_number:
                                                try:
                                                    target_line = int(line_number) - 1
                                                    if 0 <= target_line < len(self.lines):
                                                        self.cursor_y = target_line
                                                        self.cursor_x = 0
                                                        self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                        if self.cursor_y < self.scroll_y:
                                                            self.scroll_y = self.cursor_y
                                                        stdscr.addstr(max_y - 2, 0, f"Jumped to line {target_line + 1}", curses.A_BOLD)
                                                    else:
                                                        stdscr.addstr(max_y - 2, 0, f"Line {line_number} out of range (1-{len(self.lines)})")
                                                except ValueError:
                                                    stdscr.addstr(max_y - 2, 0, "Invalid number")
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                            break
                                        elif key in (curses.KEY_BACKSPACE, 127):
                                            line_number = line_number[:-1]  # Fixed: Removed 'milk'
                                        elif 48 <= key <= 57:
                                            line_number += chr(key)
                                        elif key == 27:
                                            break
                                elif command in ("replace next", "replace all"):
                                    replace_input = ""
                                    mode = "next" if command == "replace next" else "all"
                                    while True:
                                        stdscr.addstr(max_y - 2, 0, f"Replace {mode}: {replace_input}"[:max_x - 1], curses.A_BOLD)
                                        stdscr.refresh()
                                        key = stdscr.getch()
                                        if key == 10:
                                            if "/" in replace_input:
                                                parts = replace_input.split("/", 1)
                                                find_text = parts[0]
                                                replace_text = parts[1] if len(parts) > 1 else ""
                                                if find_text:
                                                    self.save_history()
                                                    if mode == "all":
                                                        for i in range(len(self.lines)):
                                                            if find_text in self.lines[i]:
                                                                self.lines[i] = self.lines[i].replace(find_text, replace_text)
                                                                self.is_modified = True
                                                        if self.is_modified:
                                                            self.cursor_y = 0
                                                            self.cursor_x = 0
                                                            self.scroll_y = 0
                                                            stdscr.addstr(max_y - 2, 0, f"Replaced all '{find_text}'", curses.A_BOLD)
                                                    else:
                                                        start_line = self.cursor_y
                                                        start_col = self.cursor_x
                                                        for i in range(start_line, len(self.lines)):
                                                            line = self.lines[i]
                                                            pos = line.find(find_text, start_col if i == start_line else 0)
                                                            if pos != -1:
                                                                self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                                self.cursor_y = i
                                                                self.cursor_x = pos + len(replace_text)
                                                                self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                                if self.cursor_y < self.scroll_y:
                                                                    self.scroll_y = self.cursor_y
                                                                self.is_modified = True
                                                                stdscr.addstr(max_y - 2, 0, f"Replaced next '{find_text}'", curses.A_BOLD)
                                                                break
                                                        else:
                                                            for i in range(start_line):
                                                                line = self.lines[i]
                                                                pos = line.find(find_text)
                                                                if pos != -1:
                                                                    self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                                    self.cursor_y = i
                                                                    self.cursor_x = pos + len(replace_text)
                                                                    self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                                    if self.cursor_y < self.scroll_y:
                                                                        self.scroll_y = self.cursor_y
                                                                    self.is_modified = True
                                                                    stdscr.addstr(max_y - 2, 0, f"Replaced next '{find_text}' (wrapped)", curses.A_BOLD)
                                                                    break
                                                            else:
                                                                stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                            else:
                                                stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                            break
                                        elif key in (curses.KEY_BACKSPACE, 127):
                                            replace_input = replace_input[:-1]
                                        elif 32 <= key <= 126:
                                            replace_input += chr(key)
                                        elif key == 27:
                                            break
                                elif command == "toggle line numbers":
                                    self.show_line_numbers = not self.show_line_numbers
                                    stdscr.addstr(max_y - 2, 0, f"Line numbers: {'on' if self.show_line_numbers else 'off'}", curses.A_BOLD)
                                elif command == "toggle word wrap":
                                    self.word_wrap = not self.word_wrap
                                    stdscr.addstr(max_y - 2, 0, f"Word wrap: {'on' if self.word_wrap else 'off'}", curses.A_BOLD)
                                elif command == "toggle syntax highlighting":
                                    self.syntax_highlighting = not self.syntax_highlighting
                                    stdscr.addstr(max_y - 2, 0, f"Syntax highlighting: {'on' if self.syntax_highlighting else 'off'}", curses.A_BOLD)
                                else:
                                    stdscr.addstr(max_y - 2, 0, f"Unknown command: {command}"[:max_x - 1], curses.A_BOLD)
                                stdscr.refresh()
                                time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                command = command[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                command += chr(key)
                            elif key == 27:  # Esc
                                stdscr.clear()
                                stdscr.addstr(max_y - 2, 0, "Palette closed", curses.A_BOLD)
                                stdscr.refresh()
                                time.sleep(0.3)
                                break
                    else:
                        stdscr.addstr(max_y - 2, 0, f"Unknown toggle: t + {chr(next_key) if 32 <= next_key <= 126 else next_key}")
                        stdscr.refresh()
                        time.sleep(0.5)
########### HOTKEY REPLACE FUNCTIONS ###############

                elif key == ord('r'):  # Replace commands
                    stdscr.timeout(-1)  # Wait indefinitely for the next key
                    next_key = stdscr.getch()
                    stdscr.timeout(300)  # Restore original timeout
                    if next_key == ord('r'):  # Replace next instance
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace next: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        start_line = self.cursor_y
                                        start_col = self.cursor_x
                                        for i in range(start_line, len(self.lines)):
                                            line = self.lines[i]
                                            pos = line.find(find_text, start_col if i == start_line else 0)
                                            if pos != -1:
                                                self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                self.cursor_y = i
                                                self.cursor_x = pos + len(replace_text)
                                                self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                if self.cursor_y < self.scroll_y:
                                                    self.scroll_y = self.cursor_y
                                                self.is_modified = True
                                                break
                                        else:
                                            # Wrap around
                                            for i in range(start_line):
                                                line = self.lines[i]
                                                pos = line.find(find_text)
                                                if pos != -1:
                                                    self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                    self.cursor_y = i
                                                    self.cursor_x = pos + len(replace_text)
                                                    self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                    if self.cursor_y < self.scroll_y:
                                                        self.scroll_y = self.cursor_y
                                                    self.is_modified = True
                                                    break
                                            else:
                                                stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('a'):  # Replace all instances
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace all: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        for i in range(len(self.lines)):
                                            if find_text in self.lines[i]:
                                                self.lines[i] = self.lines[i].replace(find_text, replace_text)
                                                self.is_modified = True
                                        if self.is_modified:
                                            self.cursor_y = 0
                                            self.cursor_x = 0
                                            self.scroll_y = 0
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('n'):  # Replace N instances
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace N: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 2)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    n = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                                    if find_text:
                                        self.save_history()
                                        count = 0
                                        start_line = self.cursor_y
                                        start_col = self.cursor_x
                                        for i in range(start_line, len(self.lines)):
                                            line = self.lines[i]
                                            pos = line.find(find_text, start_col if i == start_line else 0)
                                            while pos != -1 and count < n:
                                                self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                count += 1
                                                self.cursor_y = i
                                                self.cursor_x = pos + len(replace_text)
                                                self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                if self.cursor_y < self.scroll_y:
                                                    self.scroll_y = self.cursor_y
                                                self.is_modified = True
                                                if count == n:
                                                    break
                                                line = self.lines[i]
                                                pos = line.find(find_text, self.cursor_x)
                                            if count == n:
                                                break
                                        if count < n:
                                            # Wrap around
                                            for i in range(start_line):
                                                line = self.lines[i]
                                                pos = line.find(find_text)
                                                while pos != -1 and count < n:
                                                    self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                    count += 1
                                                    self.cursor_y = i
                                                    self.cursor_x = pos + len(replace_text)
                                                    self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                    if self.cursor_y < self.scroll_y:
                                                        self.scroll_y = self.cursor_y
                                                    self.is_modified = True
                                                    if count == n:
                                                        break
                                                    line = self.lines[i]
                                                    pos = line.find(find_text, self.cursor_x)
                                                if count == n:
                                                    break
                                            if count < n:
                                                stdscr.addstr(max_y - 2, 0, f"Only {count} of {n} '{find_text}' found"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace/N (e.g., old/new/3)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('c'):  # Replace with confirmation
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace w/ confirm: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        start_line = self.cursor_y
                                        start_col = self.cursor_x
                                        replaced = False
                                        for i in range(start_line, len(self.lines)):
                                            line = self.lines[i]
                                            pos = line.find(find_text, start_col if i == start_line else 0)
                                            while pos != -1:
                                                stdscr.addstr(max_y - 2, 0, f"Replace '{find_text}' at {i+1},{pos}? (y/n)"[:max_x - 1])
                                                stdscr.refresh()
                                                confirm = stdscr.getch()
                                                if confirm == ord('y'):
                                                    self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                    self.cursor_y = i
                                                    self.cursor_x = pos + len(replace_text)
                                                    self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                    if self.cursor_y < self.scroll_y:
                                                        self.scroll_y = self.cursor_y
                                                    self.is_modified = True
                                                    replaced = True
                                                    start_col = self.cursor_x
                                                else:
                                                    start_col = pos + len(find_text)
                                                line = self.lines[i]
                                                pos = line.find(find_text, start_col)
                                            start_col = 0
                                            if replaced and confirm != ord('y'):
                                                break
                                        if not replaced:
                                            # Wrap around
                                            for i in range(start_line):
                                                line = self.lines[i]
                                                pos = line.find(find_text)
                                                while pos != -1:
                                                    stdscr.addstr(max_y - 2, 0, f"Replace '{find_text}' at {i+1},{pos}? (y/n)"[:max_x - 1])
                                                    stdscr.refresh()
                                                    confirm = stdscr.getch()
                                                    if confirm == ord('y'):
                                                        self.lines[i] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                        self.cursor_y = i
                                                        self.cursor_x = pos + len(replace_text)
                                                        self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                        if self.cursor_y < self.scroll_y:
                                                            self.scroll_y = self.cursor_y
                                                        self.is_modified = True
                                                        replaced = True
                                                        break
                                                    pos = line.find(find_text, pos + len(find_text))
                                                if replaced:
                                                    break
                                            if not replaced:
                                                stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('w'):  # Replace in current word
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace word: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        line = self.lines[self.cursor_y]
                                        start = self.cursor_x
                                        while start > 0 and line[start - 1].isalnum():
                                            start -= 1
                                        end = self.cursor_x
                                        while end < len(line) and line[end].isalnum():
                                            end += 1
                                        word = line[start:end]
                                        if word == find_text:
                                            self.lines[self.cursor_y] = line[:start] + replace_text + line[end:]
                                            self.cursor_x = start + len(replace_text)
                                            self.is_modified = True
                                        else:
                                            stdscr.addstr(max_y - 2, 0, f"'{find_text}' not in current word"[:max_x - 1])
                                            stdscr.refresh()
                                            time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('l'):  # Replace in current line
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace in line: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        line = self.lines[self.cursor_y]
                                        if find_text in line[self.cursor_x:]:
                                            pos = line.find(find_text, self.cursor_x)
                                            self.lines[self.cursor_y] = line[:pos] + replace_text + line[pos + len(find_text):]
                                            self.cursor_x = pos + len(replace_text)
                                            self.is_modified = True
                                        else:
                                            stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found in line"[:max_x - 1])
                                            stdscr.refresh()
                                            time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new)"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    elif next_key == ord('s'):  # Replace in selection
                        replace_input = ""
                        while True:
                            stdscr.addstr(max_y - 2, 0, f"Replace in selection: {replace_input}"[:max_x - 1], curses.A_BOLD)
                            stdscr.refresh()
                            key = stdscr.getch()
                            if key == 10:  # Enter
                                if "/" in replace_input and self.selection_start and self.selection_end:
                                    parts = replace_input.split("/", 1)
                                    find_text = parts[0]
                                    replace_text = parts[1] if len(parts) > 1 else ""
                                    if find_text:
                                        self.save_history()
                                        start_y, start_x = self.selection_start
                                        end_y, end_x = self.selection_end
                                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                                        if start_y == end_y:
                                            line = self.lines[start_y]
                                            if find_text in line[start_x:end_x]:
                                                pos = line.find(find_text, start_x)
                                                if pos < end_x:
                                                    self.lines[start_y] = line[:pos] + replace_text + line[pos + len(find_text):]
                                                    self.cursor_y = start_y
                                                    self.cursor_x = pos + len(replace_text)
                                                    self.selection_end = (start_y, self.cursor_x)
                                                    self.is_modified = True
                                                else:
                                                    stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found in selection"[:max_x - 1])
                                                    stdscr.refresh()
                                                    time.sleep(0.5)
                                            else:
                                                stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found in selection"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                        else:
                                            selected_text = self.get_selected_text()
                                            if find_text in selected_text:
                                                new_lines = []
                                                for i in range(len(self.lines)):
                                                    if i < start_y or i > end_y:
                                                        new_lines.append(self.lines[i])
                                                    elif i == start_y:
                                                        line = self.lines[i]
                                                        new_lines.append(line[:start_x] + line[start_x:].replace(find_text, replace_text, 1))
                                                    elif i == end_y:
                                                        line = self.lines[i]
                                                        new_lines.append(line[:end_x].replace(find_text, replace_text) + line[end_x:])
                                                    else:
                                                        new_lines.append(self.lines[i].replace(find_text, replace_text))
                                                self.lines = new_lines
                                                self.cursor_y = end_y
                                                self.cursor_x = end_x  # Approximate, might need adjustment
                                                self.scroll_y = max(0, self.cursor_y - (max_y // 2))
                                                if self.cursor_y < self.scroll_y:
                                                    self.scroll_y = self.cursor_y
                                                self.is_modified = True
                                            else:
                                                stdscr.addstr(max_y - 2, 0, f"'{find_text}' not found in selection"[:max_x - 1])
                                                stdscr.refresh()
                                                time.sleep(0.5)
                                else:
                                    stdscr.addstr(max_y - 2, 0, "Enter find/replace (e.g., old/new) or select text"[:max_x - 1])
                                    stdscr.refresh()
                                    time.sleep(0.5)
                                break
                            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                                replace_input = replace_input[:-1]
                            elif 32 <= key <= 126:  # Printable characters
                                replace_input += chr(key)
                            elif key == 27:  # Esc to cancel
                                break
                    else:
                        stdscr.addstr(max_y - 2, 0, f"Unknown command: r + {chr(next_key) if 32 <= next_key <= 126 else next_key}"[:max_x - 1])
                        stdscr.refresh()
                        time.sleep(0.5)

###################################################
                elif key in (ord('q'), ord('Q')):
                    self.find_previous_word()
                elif key in (ord('e'), ord('E')):
                    self.find_next_word()
                elif key == 19:  # Ctrl+S
                    self.save_file(stdscr)
                elif key == 17:  # Ctrl+Q
                    break
                elif key == 18:  # Ctrl+D
                    self.save_history()
                    if len(self.lines) > 1:
                        del self.lines[self.cursor_y]
                        if self.cursor_y >= len(self.lines):
                            self.cursor_y = len(self.lines) - 1
                        self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
                    else:
                        self.lines[0] = ""
                    self.is_modified = True
                elif key == 4:  # Ctrl+D - Duplicate line or selection
                    self.save_history()  # For undo
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        selected_lines = self.lines[start_y:end_y + 1]
                        if start_y == end_y:
                            selected_text = selected_lines[0][start_x:end_x]
                            self.lines.insert(end_y + 1, selected_text)
                        else:
                            selected_lines[0] = selected_lines[0][start_x:]
                            selected_lines[-1] = selected_lines[-1][:end_x]
                            self.lines[end_y + 1:end_y + 1] = selected_lines
                        self.cursor_y = end_y + 1
                        self.cursor_x = 0
                        self.selection_start = self.selection_end = None  # Clear selection
                    else:
                        current_line = self.lines[self.cursor_y]
                        self.lines.insert(self.cursor_y + 1, current_line)
                        self.cursor_y += 1
                        self.cursor_x = 0  # Move to start of new line
                    self.is_modified = True
                elif key == 11:  # Ctrl+K
                    self.save_history()
                    line = self.lines[self.cursor_y]
                    if self.cursor_x > 0:
                        new_x = self.cursor_x
                        while new_x > 0 and not line[new_x - 1].isalnum():
                            new_x -= 1
                        while new_x > 0 and line[new_x - 1].isalnum():
                            new_x -= 1
                        self.lines[self.cursor_y] = line[:new_x] + line[self.cursor_x:]
                        self.cursor_x = new_x
                        self.is_modified = True
                elif key == 12:  # Ctrl+L
                    self.save_history()
                    line = self.lines[self.cursor_y]
                    if self.cursor_x < len(line):
                        new_x = self.cursor_x
                        while new_x < len(line) and not line[new_x].isalnum():
                            new_x += 1
                        while new_x < len(line) and line[new_x].isalnum():
                            new_x += 1
                        self.lines[self.cursor_y] = line[:self.cursor_x] + line[new_x:]
                        self.is_modified = True
                elif key == 27:  # Esc
                    self.selection_start = None
                    self.selection_end = None
                    self.is_selecting = False
                elif key == 26:  # Ctrl+Z
                    self.undo()
                elif key == 25:  # Ctrl+Y
                    self.redo()
                elif key == ord('h'):
                    self.selection_start = (self.cursor_y, 0)
                    self.selection_end = (self.cursor_y, len(self.lines[self.cursor_y]))
                    self.cursor_x = len(self.lines[self.cursor_y])
                elif key == 2:  # Ctrl+B - Paste above
                    self.save_history()
                    clipboard_text = pyperclip.paste()
                    if clipboard_text:
                        clipboard_lines = clipboard_text.splitlines()
                        if self.selection_start and self.selection_end:
                            start_y, start_x = self.selection_start
                            end_y, end_x = self.selection_end
                            if start_y > end_y or (start_y == end_y and start_x > end_x):
                                start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                            if start_y == end_y:
                                self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                            else:
                                self.lines[start_y] = self.lines[start_y][:start_x]
                                del self.lines[start_y + 1:end_y + 1]
                                self.lines[start_y] += self.lines[end_y][end_x:]
                            self.cursor_y = start_y
                            self.cursor_x = start_x
                            self.selection_start = None
                            self.selection_end = None
                            self.is_selecting = False
                        for i, line in enumerate(reversed(clipboard_lines)):
                            self.lines.insert(self.cursor_y, line)
                        self.is_modified = True
                elif key == 14:  # Ctrl+N - Paste below
                    self.save_history()
                    clipboard_text = pyperclip.paste()
                    if clipboard_text:
                        clipboard_lines = clipboard_text.splitlines()
                        if self.selection_start and self.selection_end:
                            start_y, start_x = self.selection_start
                            end_y, end_x = self.selection_end
                            if start_y > end_y or (start_y == end_y and start_x > end_x):
                                start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                            if start_y == end_y:
                                self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                            else:
                                self.lines[start_y] = self.lines[start_y][:start_x]
                                del self.lines[start_y + 1:end_y + 1]
                                self.lines[start_y] += self.lines[end_y][end_x:]
                            self.cursor_y = start_y
                            self.cursor_x = start_x
                            self.selection_start = None
                            self.selection_end = None
                            self.is_selecting = False
                        for i, line in enumerate(clipboard_lines):
                            self.lines.insert(self.cursor_y + 1 + i, line)
                        self.cursor_y += len(clipboard_lines)
                        self.cursor_x = len(clipboard_lines[-1])
                        self.is_modified = True
                elif key == ord('l'):
                    if not self.selection_start:
                        line = self.lines[self.cursor_y]
                        start_x = self.cursor_x
                        while start_x > 0 and line[start_x - 1].isalnum():
                            start_x -= 1
                        self.selection_start = (self.cursor_y, start_x)
                        end_x = self.cursor_x
                        while end_x < len(line) and line[end_x].isalnum():
                            end_x += 1
                        self.selection_end = (self.cursor_y, end_x)
                        self.cursor_x = end_x
                    else:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        line = self.lines[end_y]
                        while end_x < len(line) and not line[end_x].isalnum():
                            end_x += 1
                        if end_x < len(line):
                            while end_x < len(line) and line[end_x].isalnum():
                                end_x += 1
                            self.selection_end = (end_y, end_x)
                            self.cursor_y = end_y
                            self.cursor_x = end_x
                        elif end_y < len(self.lines) - 1:
                            end_y += 1
                            line = self.lines[end_y]
                            end_x = 0
                            while end_x < len(line) and not line[end_x].isalnum():
                                end_x += 1
                            while end_x < len(line) and line[end_x].isalnum():
                                end_x += 1
                            self.selection_end = (end_y, end_x)
                            self.cursor_y = end_y
                            self.cursor_x = end_x
                elif key == ord('k'):
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        line = self.lines[end_y]
                        if end_y > start_y or (end_y == start_y and end_x > start_x):
                            if end_x > 0:
                                new_end_x = end_x
                                while new_end_x > 0 and not line[new_end_x - 1].isalnum():
                                    new_end_x -= 1
                                while new_end_x > 0 and line[new_end_x - 1].isalnum():
                                    new_end_x -= 1
                                if end_y == start_y and new_end_x <= start_x:
                                    self.selection_start = None
                                    self.selection_end = None
                                    self.cursor_y = start_y
                                    self.cursor_x = start_x
                                elif new_end_x > 0:
                                    temp_x = new_end_x
                                    while temp_x > 0 and not line[temp_x - 1].isalnum():
                                        temp_x -= 1
                                    while temp_x < len(line) and line[temp_x].isalnum():
                                        temp_x += 1
                                    self.selection_end = (end_y, temp_x)
                                    self.cursor_y = end_y
                                    self.cursor_x = temp_x
                                else:
                                    if end_y > 0:
                                        end_y -= 1
                                        line = self.lines[end_y]
                                        end_x = len(line)
                                        while end_x > 0 and not line[end_x - 1].isalnum():
                                            end_x -= 1
                                        while end_x > 0 and line[end_x - 1].isalnum():
                                            end_x -= 1
                                        while end_x < len(line) and line[end_x].isalnum():
                                            end_x += 1
                                        self.selection_end = (end_y, end_x)
                                        self.cursor_y = end_y
                                        self.cursor_x = end_x
                                    else:
                                        self.selection_start = None
                                        self.selection_end = None
                                        self.cursor_y = start_y
                                        self.cursor_x = start_x
                            elif end_y > 0:
                                end_y -= 1
                                line = self.lines[end_y]
                                end_x = len(line)
                                while end_x > 0 and not line[end_x - 1].isalnum():
                                    end_x -= 1
                                while end_x > 0 and line[end_x - 1].isalnum():
                                    end_x -= 1
                                while end_x < len(line) and line[end_x].isalnum():
                                    end_x += 1
                                self.selection_end = (end_y, end_x)
                                self.cursor_y = end_y
                                self.cursor_x = end_x
                            else:
                                self.selection_start = None
                                self.selection_end = None
                                self.cursor_y = start_y
                                self.cursor_x = start_x
                elif key == 24:  # Ctrl+X
                    selected_text = self.get_selected_text()
                    if selected_text:
                        self.save_history()
                        pyperclip.copy(selected_text)
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            self.lines[start_y] = self.lines[start_y][:start_x]
                            del self.lines[start_y + 1:end_y + 1]
                            self.lines[start_y] += self.lines[end_y][end_x:]
                        self.cursor_y, self.cursor_x = start_y, start_x
                        self.selection_start = self.selection_end = None
                        self.is_modified = True
                elif key == 3:  # Ctrl+C
                    selected_text = self.get_selected_text()
                    if selected_text:
                        pyperclip.copy(selected_text)
                elif key == 22:  # Ctrl+V
                    self.save_history()
                    clipboard_text = pyperclip.paste()
                    if clipboard_text:
                        clipboard_lines = clipboard_text.splitlines()
                        if self.selection_start and self.selection_end:
                            start_y, start_x = self.selection_start
                            end_y, end_x = self.selection_end
                            if start_y > end_y or (start_y == end_y and start_x > end_x):
                                start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                            # Capture remaining end before deletion
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            if start_y == end_y:
                                self.lines[start_y] = self.lines[start_y][:start_x] + clipboard_lines[0] + self.lines[start_y][end_x:]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + len(clipboard_lines[0])
                            else:
                                self.lines[start_y] = self.lines[start_y][:start_x] + clipboard_lines[0]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + len(clipboard_lines[0])
                                if len(clipboard_lines) > 1:
                                    self.lines[start_y + 1:start_y + 1] = clipboard_lines[1:-1]
                                    self.lines.insert(start_y + len(clipboard_lines) - 1, clipboard_lines[-1] + remaining_end)
                                    self.cursor_y = start_y + len(clipboard_lines) - 1
                                    self.cursor_x = len(clipboard_lines[-1])
                                if end_y >= start_y + 1:
                                    del self.lines[start_y + len(clipboard_lines):end_y + 1]
                            self.selection_start = None
                            self.selection_end = None
                            self.is_selecting = False
                        else:
                            if len(clipboard_lines) == 1:
                                self.lines[self.cursor_y] = (
                                    self.lines[self.cursor_y][:self.cursor_x] +
                                    clipboard_lines[0] +
                                    self.lines[self.cursor_y][self.cursor_x:]
                                )
                                self.cursor_x += len(clipboard_lines[0])
                            else:
                                first_line = clipboard_lines[0]
                                last_line = clipboard_lines[-1]
                                middle_lines = clipboard_lines[1:-1]
                                remaining = self.lines[self.cursor_y][self.cursor_x:]
                                self.lines[self.cursor_y] = self.lines[self.cursor_y][:self.cursor_x] + first_line
                                for line in middle_lines:
                                    self.cursor_y += 1
                                    self.lines.insert(self.cursor_y, line)
                                self.cursor_y += 1
                                self.lines.insert(self.cursor_y, last_line + remaining)
                                self.cursor_x = len(last_line)
                        self.is_modified = True
                elif key == 1:  # Ctrl+A
                    if self.lines:
                        self.selection_start = (0, 0)
                        self.selection_end = (len(self.lines) - 1, len(self.lines[-1]))
                elif key == 9:  # Tab
                    self.save_history()
                    self.lines[self.cursor_y] = (
                        self.lines[self.cursor_y][:self.cursor_x] + "    " + self.lines[self.cursor_y][self.cursor_x:]
                    )
                    self.cursor_x += 4
                    self.is_modified = True
                elif key in (curses.KEY_BACKSPACE, 127):  # Backspace
                    self.save_history()
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            self.lines[start_y] = self.lines[start_y][:start_x] + remaining_end
                            del self.lines[start_y + 1:end_y + 1]
                        self.cursor_y = start_y
                        self.cursor_x = start_x
                        self.selection_start = None
                        self.selection_end = None
                        self.is_selecting = False
                    elif self.cursor_x > 0:
                        self.lines[self.cursor_y] = (
                            self.lines[self.cursor_y][:self.cursor_x - 1] + self.lines[self.cursor_y][self.cursor_x:]
                        )
                        self.cursor_x -= 1
                    elif self.cursor_y > 0:
                        prev_line_length = len(self.lines[self.cursor_y - 1])
                        self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
                        del self.lines[self.cursor_y]
                        self.cursor_y -= 1
                        self.cursor_x = prev_line_length
                    self.is_modified = True
                elif key == curses.KEY_DC:  # Delete
                    self.save_history()
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            self.lines[start_y] = self.lines[start_y][:start_x] + remaining_end
                            del self.lines[start_y + 1:end_y + 1]
                        self.cursor_y = start_y
                        self.cursor_x = start_x
                        self.selection_start = None
                        self.selection_end = None
                        self.is_selecting = False
                    elif self.cursor_x < len(self.lines[self.cursor_y]):
                        self.lines[self.cursor_y] = (
                            self.lines[self.cursor_y][:self.cursor_x] + self.lines[self.cursor_y][self.cursor_x + 1:]
                        )
                    elif self.cursor_y < len(self.lines) - 1:
                        self.lines[self.cursor_y] += self.lines[self.cursor_y + 1]
                        del self.lines[self.cursor_y + 1]
                    self.is_modified = True
                elif key == 10:  # Enter
                    self.save_history()
                    current_line = self.lines[self.cursor_y]
                    indentation = ""
                    for char in current_line:
                        if char in (" ", "\t"):
                            indentation += char
                        else:
                            break
                    if self.should_increase_indentation(current_line):
                        indentation += "    "
                    elif self.should_decrease_indentation(current_line):
                        indentation = indentation[:-4]
                    new_line = current_line[self.cursor_x:]
                    self.lines[self.cursor_y] = current_line[:self.cursor_x]
                    self.lines.insert(self.cursor_y + 1, indentation + new_line)
                    self.cursor_y += 1
                    self.cursor_x = len(indentation)
                    self.is_modified = True

                elif key == 6:  # Ctrl+F - Search
                    self.is_searching = True
                    self.search_query = ""
                    self.search_results = []
                    self.search_index = -1
                elif key == 32:  # Space to enter WRITE mode
                    self.is_writing = True

            # WRITE mode
            else:
                if key in (curses.KEY_BACKSPACE, 127):  # Backspace
                    self.save_history()
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            self.lines[start_y] = self.lines[start_y][:start_x] + remaining_end
                            del self.lines[start_y + 1:end_y + 1]
                        self.cursor_y = start_y
                        self.cursor_x = start_x
                        self.selection_start = None
                        self.selection_end = None
                        self.is_selecting = False
                    elif self.cursor_x > 0:
                        self.lines[self.cursor_y] = (
                            self.lines[self.cursor_y][:self.cursor_x - 1] + self.lines[self.cursor_y][self.cursor_x:]
                        )
                        self.cursor_x -= 1
                    elif self.cursor_y > 0:
                        prev_line_length = len(self.lines[self.cursor_y - 1])
                        self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
                        del self.lines[self.cursor_y]
                        self.cursor_y -= 1
                        self.cursor_x = prev_line_length
                    self.is_modified = True
                elif key == curses.KEY_DC:  # Delete
                    self.save_history()
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            self.lines[start_y] = self.lines[start_y][:start_x] + remaining_end
                            del self.lines[start_y + 1:end_y + 1]
                        self.cursor_y = start_y
                        self.cursor_x = start_x
                        self.selection_start = None
                        self.selection_end = None
                        self.is_selecting = False
                    elif self.cursor_x < len(self.lines[self.cursor_y]):
                        self.lines[self.cursor_y] = (
                            self.lines[self.cursor_y][:self.cursor_x] + self.lines[self.cursor_y][self.cursor_x + 1:]
                        )
                    elif self.cursor_y < len(self.lines) - 1:
                        self.lines[self.cursor_y] += self.lines[self.cursor_y + 1]
                        del self.lines[self.cursor_y + 1]
                    self.is_modified = True
                elif 32 <= key <= 126:  # Printable characters
                        self.save_history()
                        if self.selection_start and self.selection_end:
                            start_y, start_x = self.selection_start
                            end_y, end_x = self.selection_end
                            if start_y > end_y or (start_y == end_y and start_x > end_x):
                                start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                            if start_y == end_y:
                                self.lines[start_y] = self.lines[start_y][:start_x] + chr(key) + self.lines[start_y][end_x:]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + 1
                            else:
                                remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                                self.lines[start_y] = self.lines[start_y][:start_x] + chr(key) + remaining_end
                                if end_y >= start_y + 1:
                                    del self.lines[start_y + 1:end_y + 1]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + 1
                            self.selection_start = None
                            self.selection_end = None
                            self.is_selecting = False
                        else:
                            self.lines[self.cursor_y] = (
                                self.lines[self.cursor_y][:self.cursor_x] +
                                chr(key) +
                                self.lines[self.cursor_y][self.cursor_x:]
                            )
                            self.cursor_x += 1
                        self.is_modified = True
                elif key == 10:  # Enter
                    self.save_history()
                    current_line = self.lines[self.cursor_y]
                    indentation = ""
                    for char in current_line:
                        if char in (" ", "\t"):
                            indentation += char
                        else:
                            break
                    if self.should_increase_indentation(current_line):
                        indentation += "    "
                    elif self.should_decrease_indentation(current_line):
                        indentation = indentation[:-4]
                    new_line = current_line[self.cursor_x:]
                    self.lines[self.cursor_y] = current_line[:self.cursor_x]
                    self.lines.insert(self.cursor_y + 1, indentation + new_line)
                    self.cursor_y += 1
                    self.cursor_x = len(indentation)
                    self.is_modified = True
                elif key == 22:  # Ctrl+V
                    self.save_history()
                    clipboard_text = pyperclip.paste()
                    if clipboard_text:
                        clipboard_lines = clipboard_text.splitlines()
                        if self.selection_start and self.selection_end:
                            start_y, start_x = self.selection_start
                            end_y, end_x = self.selection_end
                            if start_y > end_y or (start_y == end_y and start_x > end_x):
                                start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                            # Capture remaining end before deletion
                            remaining_end = self.lines[end_y][end_x:] if end_y < len(self.lines) else ""
                            if start_y == end_y:
                                self.lines[start_y] = self.lines[start_y][:start_x] + clipboard_lines[0] + self.lines[start_y][end_x:]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + len(clipboard_lines[0])
                            else:
                                self.lines[start_y] = self.lines[start_y][:start_x] + clipboard_lines[0]
                                self.cursor_y = start_y
                                self.cursor_x = start_x + len(clipboard_lines[0])
                                if len(clipboard_lines) > 1:
                                    self.lines[start_y + 1:start_y + 1] = clipboard_lines[1:-1]
                                    self.lines.insert(start_y + len(clipboard_lines) - 1, clipboard_lines[-1] + remaining_end)
                                    self.cursor_y = start_y + len(clipboard_lines) - 1
                                    self.cursor_x = len(clipboard_lines[-1])
                                if end_y >= start_y + 1:
                                    del self.lines[start_y + len(clipboard_lines):end_y + 1]
                            self.selection_start = None
                            self.selection_end = None
                            self.is_selecting = False
                        else:
                            if len(clipboard_lines) == 1:
                                self.lines[self.cursor_y] = (
                                    self.lines[self.cursor_y][:self.cursor_x] +
                                    clipboard_lines[0] +
                                    self.lines[self.cursor_y][self.cursor_x:]
                                )
                                self.cursor_x += len(clipboard_lines[0])
                            else:
                                first_line = clipboard_lines[0]
                                last_line = clipboard_lines[-1]
                                middle_lines = clipboard_lines[1:-1]
                                remaining = self.lines[self.cursor_y][self.cursor_x:]
                                self.lines[self.cursor_y] = self.lines[self.cursor_y][:self.cursor_x] + first_line
                                for line in middle_lines:
                                    self.cursor_y += 1
                                    self.lines.insert(self.cursor_y, line)
                                self.cursor_y += 1
                                self.lines.insert(self.cursor_y, last_line + remaining)
                                self.cursor_x = len(last_line)
                        self.is_modified = True
                elif key == curses.KEY_UP:
                    self.cursor_y = max(0, self.cursor_y - 1)
                elif key == curses.KEY_DOWN:
                    self.cursor_y = min(len(self.lines) - 1, self.cursor_y + 1)
                elif key == curses.KEY_LEFT:
                    self.cursor_x = max(0, self.cursor_x - 1)
                elif key == curses.KEY_RIGHT:
                    self.cursor_x = min(len(self.lines[self.cursor_y]), self.cursor_x + 1)
                elif key == curses.KEY_HOME:
                    self.cursor_x = 0
                elif key == curses.KEY_END:
                    self.cursor_x = len(self.lines[self.cursor_y])
                elif key == curses.KEY_PPAGE:
                    self.scroll_y = max(0, self.scroll_y - (max_y - 1))
                    self.cursor_y = max(0, self.cursor_y - (max_y - 1))
                elif key == curses.KEY_NPAGE:
                    self.scroll_y = min(max(0, len(self.lines) - (max_y - 1)), self.scroll_y + (max_y - 1))
                    self.cursor_y = min(len(self.lines) - 1, self.cursor_y + (max_y - 1))
                elif key == 19:  # Ctrl+S
                    self.save_file(stdscr)
                elif key == 17:  # Ctrl+Q
                    break
                elif key == 18:  # Ctrl+D
                    self.save_history()
                    if len(self.lines) > 1:
                        del self.lines[self.cursor_y]
                        if self.cursor_y >= len(self.lines):
                            self.cursor_y = len(self.lines) - 1
                        self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
                    else:
                        self.lines[0] = ""
                    self.is_modified = True
                elif key == 4:  # Ctrl+D - Duplicate line or selection
                    self.save_history()  # For undo
                    if self.selection_start and self.selection_end:
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        selected_lines = self.lines[start_y:end_y + 1]
                        if start_y == end_y:
                            selected_text = selected_lines[0][start_x:end_x]
                            self.lines.insert(end_y + 1, selected_text)
                        else:
                            selected_lines[0] = selected_lines[0][start_x:]
                            selected_lines[-1] = selected_lines[-1][:end_x]
                            self.lines[end_y + 1:end_y + 1] = selected_lines
                        self.cursor_y = end_y + 1
                        self.cursor_x = 0
                        self.selection_start = self.selection_end = None  # Clear selection
                    else:
                        current_line = self.lines[self.cursor_y]
                        self.lines.insert(self.cursor_y + 1, current_line)
                        self.cursor_y += 1
                        self.cursor_x = 0  # Move to start of new line
                    self.is_modified = True
                elif key == 23:  # Ctrl+W
                    self.save_history()
                    line = self.lines[self.cursor_y]
                    if self.cursor_x > 0:
                        new_x = self.cursor_x
                        while new_x > 0 and not line[new_x - 1].isalnum():
                            new_x -= 1
                        while new_x > 0 and line[new_x - 1].isalnum():
                            new_x -= 1
                        self.lines[self.cursor_y] = line[:new_x] + line[self.cursor_x:]
                        self.cursor_x = new_x
                        self.is_modified = True
                elif key == 26:  # Ctrl+Z
                    self.undo()
                elif key == 25:  # Ctrl+Y
                    self.redo()
                elif key == 24:  # Ctrl+X
                    selected_text = self.get_selected_text()
                    if selected_text:
                        self.save_history()
                        pyperclip.copy(selected_text)
                        start_y, start_x = self.selection_start
                        end_y, end_x = self.selection_end
                        if start_y > end_y or (start_y == end_y and start_x > end_x):
                            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
                        if start_y == end_y:
                            self.lines[start_y] = self.lines[start_y][:start_x] + self.lines[start_y][end_x:]
                        else:
                            self.lines[start_y] = self.lines[start_y][:start_x]
                            del self.lines[start_y + 1:end_y + 1]
                            self.lines[start_y] += self.lines[end_y][end_x:]
                        self.cursor_y, self.cursor_x = start_y, start_x
                        self.selection_start = self.selection_end = None
                        self.is_modified = True
                elif key == 3:  # Ctrl+C
                    selected_text = self.get_selected_text()
                    if selected_text:
                        pyperclip.copy(selected_text)
                elif key == 1:  # Ctrl+A
                    if self.lines:
                        self.selection_start = (0, 0)
                        self.selection_end = (len(self.lines) - 1, len(self.lines[-1]))
                elif key == 9:  # Tab
                    self.save_history()
                    self.lines[self.cursor_y] = (
                        self.lines[self.cursor_y][:self.cursor_x] + "    " + self.lines[self.cursor_y][self.cursor_x:]
                    )
                    self.cursor_x += 4
                    self.is_modified = True

                elif key == 6:  # Ctrl+F - Search
                    self.is_searching = True
                    self.search_query = ""
                    self.search_results = []
                    self.search_index = -1
                elif key == 27:  # Esc to exit WRITE mode
                    self.is_writing = False

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    editor = Kale(filename)
    curses.wrapper(editor.run)