# Sokoban

Run sokoban in the terminal.

```bash
python sokoban.py --level level01
```

[![asciicast](https://asciinema.org/a/lUbfsMN1OvdCp0bgEKprNbptY.svg)](https://asciinema.org/a/lUbfsMN1OvdCp0bgEKprNbptY)

The levels are plain text files with the map represented as a grid of tiles. The tiles can be of specific types according to the table below. It is possible for a tile to be of type cross and box or cross and player at the same time. The code for such tiles are the sum of the individual codes (3 for cross+box and 5 for cross+player).

| type   | code | description                                               |
| ------ | ---- | --------------------------------------------------------- |
| clear  | 0    | A tile that can contain a box or a player, that is empty. |
| cross  | 1    | A tile that should contain a box to win the game.         |
| box    | 2    | A tile that contains a box.                               |
| player | 4    | A tile that contains a player.                            |
| empty  | 6    | A tile that cannot contain anything.                      |
