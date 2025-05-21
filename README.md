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

Basic controls:
Space - Enter WRITE mode to input text
ESC - Exit WRITE mode and enter COMMAND mode
Ctrl + Q - Exit without saving
Ctrl + S - Save file
Ctrl + C - Copy text
Ctrl + V - Paste text

Controls for COMMAND mode
Space - Enter WRITE mode
W - Move up one character
S - Move down one character
A - Move left one character
D - Move right one character
Q - Move back one word
E - Move forward one word

Controls for WRITE mode
ESC - Exit WRITE mode
