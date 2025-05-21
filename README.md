# kale-text-editor
I love Nano, I wanted to love Vim, but couldn't so I made my own text editor called K.A.L.E. or "Keegan's Awful Lite Editor".

Contact info : cautiousdollop@protonmail.com

Current state - Massively Unfinished, but surprisingly functional.
KALE is Open Source, but I'm not in a position to accept contributions to the code at the moment as this is just a small project I sometimes work on if I feel like it.

Installation instructions:
  1. mv kale.py kale
  2. chmod +x kale
  3. sudo mv kale /usr/local/bin/kale
     OR FOR SINGLE USER
     mkdir -p ~/.local/bin
     mv kale ~/.local/bin/kale
  4. export PATH="$HOME/.local/bin:$PATH"
  5. source ~/.bashrc
  6. Type "kale test.txt" and make sure it works.
  7. Figure out how to escape my Vim clone.

Better Control documentation comming soon... Mouse use is still very basic. There are plenty more controls I just need to fully write down what each thing does.

Controls
Kale operates in two main modes: COMMAND mode (for navigation and actions) and WRITE mode (for text editing). Switch between them with the Spacebar. Here’s the full breakdown of keybindings and mouse interactions:

General Controls
These work in both modes unless specified.

Spacebar: Enter WRITE mode from COMMAND mode.
ESC: Enters COMMAND mode from WRITE mode and leaves most other modes (Search, Selection, Toggle Help)
Ctrl+S: Save the file.
Ctrl+Q: Quit the editor.
Ctrl+Z: Undo the last change.
Ctrl+Y: Redo the last undone change.
Ctrl+F: Enter search mode.
COMMAND Mode - Used for quick navigation and edits
WRITE Mode - Used for basic writing tasks, has most functionality of a regular text-editor

W: Move cursor up.
A: Move cursor left.
S: Move cursor down.
D: Move cursor right.
Q: Jump to the start of the previous word.
E: Jump to the start of the next word.
J + [key]: Jump commands:
  J + Q: Top of the file.
  J + E: Bottom of the file.
  J + W: Page up.
  J + S: Page down.
  J + A: Start of the current line.
  J + D: End of the current line.
  J + K: Half page up.
  J + L: Half page down.
  J + J: Jump to a specific line number (enter the number afterward).
T + [key]: Toggle commands:
  T + N: Toggle line numbers on/off.
  T + M: Toggle word wrap on/off.
  T + S: Toggle syntax highlighting on/off.
  T + A: Toggle auto-save on/off.
  T + O: Toggle mouse support on/off.
  T + B: Toggle status bar on/off.
  T + H: Toggle help screen on/off.
  T + C: Toggle comments on selected lines.
  T + U: Uncomment selected lines.
H: Select the current line.
L: Extend selection to the next word.
K: Shrink selection from the end.
Ctrl+D: Delete the current line or selected text.
Ctrl+K: Delete from cursor to the start of the current word.
Ctrl+L: Delete from cursor to the end of the current word.
Ctrl+X: Cut selected text to clipboard.
Ctrl+C: Copy selected text to clipboard.
Ctrl+V: Paste clipboard text at cursor (replaces selection if active).
Ctrl+A: Select all text.
Tab: Insert four spaces.
Backspace: Delete character before cursor or selected text; merge with previous line if at line start.
Delete: Delete character at cursor or selected text; merge with next line if at line end.
Enter: Insert a new line with auto-indentation based on language rules.

WRITE Mode
Edit text directly.

Printable Characters (A-Z, 0-9, symbols): Insert the character at the cursor (replaces selection if active).
Backspace: Delete character before cursor or selected text; merge with previous line if at line start.
Delete: Delete character at cursor or selected text; merge with next line if at line end.
Enter: Insert a new line with auto-indentation (e.g., extra indent after : in Python).
Arrow Keys:
Up: Move cursor up one line.
Down: Move cursor down one line.
Left: Move cursor left one character.
Right: Move cursor right one character.
Home: Move cursor to start of the line.
End: Move cursor to end of the line.
Page Up: Scroll up one page.
Page Down: Scroll down one page.
Ctrl+V: Paste clipboard text at cursor (replaces selection if active).
Ctrl+D: Duplicate the current line or selected text below.
Ctrl+W: Delete from cursor to the start of the current word.
Ctrl+X: Cut selected text to clipboard.
Ctrl+C: Copy selected text to clipboard.
Ctrl+A: Select all text.
Tab: Insert four spaces.
Mouse Controls
Available when mouse support is enabled (default: on; toggle with T + O).

Left Click: Move cursor to clicked position or start a selection.
Double Left Click: Select the word under the cursor.
Drag Left Click: Extend selection to the dragged position.
Scroll Wheel Up: Scroll up three lines.
Scroll Wheel Down: Scroll down three lines.
Search Mode
Activated with Ctrl+F.

Ctrl+F: Enter search mode.
Printable Characters: Add to the search query.
Enter: Confirm search and exit search mode.
Esc: Cancel search and clear query.
Up Arrow: Move to previous search result.
Down Arrow: Move to next search result.
Backspace: Remove last character from query and update results.
