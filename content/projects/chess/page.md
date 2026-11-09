## What it is

A chess game for two players on one computer, with a board drawn in pygame: click a piece, then the square to move it to, with the side to move shown on screen.

## Design

The rules are written as an object-oriented model kept separate from the interface: a `Board` holds the grid of pieces and the player to move, and an abstract `Piece` class (with its FEN character, colour and movement directions) is implemented by the King, Queen, Bishop, Rook, Knight and Pawn. Colours and FEN symbols are dataclasses.
