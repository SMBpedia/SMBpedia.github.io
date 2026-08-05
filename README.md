# SMBpedia.github.io

## Editing pages

1. Clone the repository or download `editor.py`, `template.html`, `style.css`, and `dictionary.txt`

2. Install the required python libraries: `pip install PySide6 markdown beautifulsoup4 pyspellchecker`

    2a. Possible requirements on Linux: `sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0`
3. Run the editor with `python editor.py`

4. In the editor you can open pages, edit them in markdown on the left side, view the formatted webpage on the right, and then save them as an html file.

    4a. See [Markdown Cheat Sheet](https://www.markdownguide.org/cheat-sheet/) for formatting help. The editor supports all basic and most extended features. 

5. Commit changes and push them to github. Uploading files to github with the web interface works fine also.

## Style guide

Generally follow the [Wikipedia style guide](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style).

Notably, page titles and sections should be in sentence case (i.e. only first word capitalized). File names should match page titles but with spaces replaced with underscores. Also, links to other pages should not include .html.
