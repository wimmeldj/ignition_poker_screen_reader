# Ignition/Bovada Poker Screen Reader

### Description

This was written to TEST the feasibility of implementing a heads up display (HUD) for ignition/bovada
games using only opencv for pattern matching, numpy for image array comparison, and tesseract ocr for optical
character recognition.

It currently detects when a game is running, parses the big blind size, sb size, handedness 
(heads up, six handed, or nine handed), the seat numbers of each player, and the stack sizes of each
player.

The config is currently set to debug mode and will print all the information above for each running table
to the terminal. This only runs on windows because it requires the win32gui library to screenshot each
poker game running.

### Dependencies

- [Tesseract OCR for Windows v3.05.01](https://digi.bib.uni-mannheim.de/tesseract/) v4.0 and up don't work yet. Binary for 3.05.01 is also provided in /dependency_binaries. Install it on your system and add 'tesseract' to your path pointing to the install location of the binary.
- [PyWin32](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pywin32) This is where the win32gui lib comes from.
Binary for python 3.7 64 bit is also provided in /dependency_binaries. Install it with pip.
- numpy
- opencv-python
- Pillow
- pytesseract
- python 3.6 or higher

### Current State

Because we can't fork processes on windows, the initialization of the poker tables is slower than it would
on a unix-like system. 

Current timings for table initialization when run in a 64bit windows 10 vm with 6 cpus and 8gb of ram
(reading bb size, sb size, handedness, player seats and relative stack sizes):
    - 1 table < 1.5 sec.
    - 3 tables < 3 sec.
    - 6 tables ~ 5 sec.

This isn't terrible and a HUD might be feasible. Using tesseract ocr for parsing text (stack sizes and pot sizes
mainly) might be impacting performance more than something like a trie which would store the actual bitmaps of characters. But
using tesseract also makes adapting to changes in the poker table display much simpler. 

Additionally, we won't need to constantly run ocr operations on every player's stack size. If we always keep track of pot size,
the players involved in a hand, and the outcome of a hand, we can avoid this. 

Writing this type of application is also difficult for a poker client like Bovada's because their application displays zero
informative text real time. It's entirely visual. So for example, when a player wins a hand, the application doesn't display 
"player x wins pot $xx.xx with Ace high." Instead, you simply see the player turn over his hand and the pot visually transfer
over to the player (and his stack increase by the pot size - rake). 

