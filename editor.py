import sys
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup, Comment

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


TEMPLATE_FILE = "template.html"


def slugify(text):
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Markdown HTML Editor")
        self.resize(1500, 900)

        self.template = Path(TEMPLATE_FILE).read_text(encoding="utf8")

        self.editor = QTextEdit()

        self.preview = QWebEngineView()

        self.open_button = QPushButton("Open HTML")
        self.save_button = QPushButton("Save HTML")

        left = QVBoxLayout()
        left.addWidget(self.editor)

        buttons = QHBoxLayout()
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.save_button)

        left.addLayout(buttons)

        layout = QHBoxLayout()
        layout.addLayout(left, 1)
        layout.addWidget(self.preview, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_preview)

        self.editor.textChanged.connect(self.queue_update)
        self.open_button.clicked.connect(self.open_html)
        self.save_button.clicked.connect(self.save_html)

        self.editor.setPlainText(
"""# Page Title

Some introductory text.

## Section One

Some text.

### Subheading

More text.

## Another Section

Even more text.
"""
        )

        self.update_preview()

    def queue_update(self):
        self.timer.start(100)

    def markdown_to_html(self, md):

        html = markdown.markdown(
            md,
            extensions=[
                "extra",
                "sane_lists",
            ],
        )

        article = BeautifulSoup(html, "html.parser")
        
        for img in article.find_all("img"):
            wrapper = article.new_tag("div")
            wrapper["class"] = "articleRight"

            inner = article.new_tag("div")
            inner["class"] = "articleRightInner"

            new_img = article.new_tag("img")
            new_img["src"] = img.get("src", "")

            # Preserve other attributes if present
            if img.get("title"):
                new_img["title"] = img["title"]

            if img.get("width"):
                new_img["width"] = img["width"]

            if img.get("height"):
                new_img["height"] = img["height"]

            inner.append(new_img)
            wrapper.append(inner)

            alt = img.get("alt", "")
            if alt:
                wrapper.append(alt)

            img.replace_with(wrapper)

        h1 = article.find("h1")
        page_title = h1.get_text() if h1 else "Untitled"

        sections = []

        current = None

        for child in list(article.children):

            if getattr(child, "name", None) == "h2":
                sid = slugify(child.get_text())

                section = article.new_tag("section")
                section["id"] = sid

                child.extract()
                section.append(child)

                article.append(section)

                current = section
                sections.append((sid, child.get_text()))
                continue

            if current is not None:
                child.extract()
                current.append(child)

        return page_title, article, sections

    def build_html(self):

        title, article, toc = self.markdown_to_html(
            self.editor.toPlainText()
        )

        soup = BeautifulSoup(self.template, "html.parser")

        md = self.editor.toPlainText()

        # "-->" isn't allowed inside HTML comments
        md = md.replace("-->", "--&gt;")

        comment = Comment("MARKDOWN\n" + md + "\nMARKDOWN")

        if soup.html:
            soup.html.insert(0, comment)
        else:
            soup.insert(0, comment)
        
        soup.title.string = title

        article_div = soup.find("div", class_="article")
        article_div.clear()

        for element in list(article.contents):
            article_div.append(element)

        ul = soup.find("div", class_="contentsPanel").find("ul")
        ul.clear()

        for i, (sid, name) in enumerate(toc, start=1):
            li = soup.new_tag("li")

            span = soup.new_tag("span")
            span.string = str(i)

            a = soup.new_tag("a", href="#" + sid)
            a.string = name

            li.append(span)
            li.append(a)

            ul.append(li)

        return str(soup)

    def update_preview(self):
        html = self.build_html()

        base = Path(".").absolute().as_uri() + "/"

        self.preview.setHtml(html, baseUrl=base)

    def save_html(self):

        title, _, _ = self.markdown_to_html(self.editor.toPlainText())

        default_name = slugify(title) + ".html"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML",
            default_name,
            "HTML (*.html)",
        )

        if not filename:
            return

        Path(filename).write_text(
            self.build_html(),
            encoding="utf8",
        )
        
    def open_html(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open HTML",
            "",
            "HTML (*.html)"
        )

        if not filename:
            return

        html = Path(filename).read_text(encoding="utf8")

        soup = BeautifulSoup(html, "html.parser")

        for node in soup.find_all(string=lambda t: isinstance(t, Comment)):
            text = str(node)

            if text.startswith("MARKDOWN\n") and text.endswith("\nMARKDOWN"):
                md = text[len("MARKDOWN\n"):-len("\nMARKDOWN")]
                md = md.replace("--&gt;", "-->")

                # Prevent lots of unnecessary preview updates while loading
                self.editor.blockSignals(True)
                self.editor.setPlainText(md)
                self.editor.blockSignals(False)

                self.update_preview()
                return

        QMessageBox.warning(
            self,
            "Markdown Not Found",
            "This HTML file does not contain embedded markdown."
        )


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
