"""
Help dialog module for ORFOCODE spelling trainer.
Loads markdown documentation with images from local folder.
"""

import os
import sys
import re
import markdown
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton,
    QHBoxLayout, QApplication, QWidget, QSplitter,
    QListWidget, QListWidgetItem
)
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PySide6.QtCore import Qt, QUrl


class HelpDialog(QDialog):
    """
    A dialog that displays help content from a Markdown file with a sidebar table of contents.
    """

    def __init__(self, parent=None, help_file_path=None):
        super().__init__(parent)

        # Paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.help_file_path = help_file_path or os.path.join(base_dir, "help.md")
        self.images_path = os.path.join(base_dir, "images")

        self.setWindowTitle("Справка — ORFOCODE")
        self.resize(1000, 950)

        self._setup_ui()
        self._load_help()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Create splitter for table of contents and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Table of contents widget (left sidebar)
        toc_container = QWidget()
        toc_container_layout = QVBoxLayout(toc_container)
        toc_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.toc_widget = QListWidget()
        self.toc_widget.setMinimumWidth(200)
        self.toc_widget.setMaximumWidth(350)
        self.toc_widget.itemClicked.connect(self._on_toc_item_clicked)
        
        # Add title to TOC sidebar
        toc_title = QListWidgetItem("📚 Содержание")
        toc_title.setFlags(toc_title.flags() & ~Qt.ItemIsSelectable)  # Make non-selectable
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        toc_title.setFont(font)
        toc_title.setBackground(QColor(240, 240, 240))
        self.toc_widget.addItem(toc_title)
        
        toc_container_layout.addWidget(self.toc_widget)
        splitter.addWidget(toc_container)
        
        # Content widget (right side)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setOpenLinks(True)
        self.text_browser.anchorClicked.connect(self._on_anchor_clicked)
        
        font = QFont("Arial", 11)
        self.text_browser.setFont(font)
        
        content_layout.addWidget(self.text_browser)
        splitter.addWidget(content_widget)
        
        # Set initial splitter sizes (30% for TOC, 70% for content)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)

        # Close and Refresh buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self._load_help)
        btn_layout.addWidget(btn_refresh)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def _on_toc_item_clicked(self, item):
        """Scroll to section when TOC item is clicked."""
        # Skip the title item (first item)
        if self.toc_widget.row(item) == 0:
            return
            
        if hasattr(item, 'anchor'):
            self.text_browser.scrollToAnchor(item.anchor)
            
    def _on_anchor_clicked(self, url):
        """Handle anchor clicks within the document."""
        if url.toString().startswith("#"):
            self.text_browser.scrollToAnchor(url.toString()[1:])

    def _extract_headings_and_add_anchors(self, html_text):
        """
        Extract headings from HTML and add anchors.
        Returns: (modified_html, toc_items)
        """
        # Regex to find headings (h1-h3)
        heading_pattern = re.compile(r'<h([1-3])>(.*?)</h\1>', re.DOTALL)
        
        toc_items = []  # List of (level, text, anchor)
        modified_html = html_text
        anchor_counter = 0
        
        # Find all headings and add anchors
        for match in heading_pattern.finditer(html_text):
            level = int(match.group(1))
            heading_text = match.group(2).strip()
            
            # Create anchor name
            anchor_name = f"section_{anchor_counter}"
            anchor_counter += 1
            
            # Replace heading with anchored version
            anchored_heading = f'<h{level}><a name="{anchor_name}"></a>{heading_text}</h{level}>'
            modified_html = modified_html.replace(match.group(0), anchored_heading, 1)
            
            # Clean heading text (remove HTML tags if any)
            clean_text = re.sub(r'<[^>]*>', '', heading_text)
            toc_items.append((level, clean_text, anchor_name))
        
        return modified_html, toc_items

    def _populate_toc_widget(self, toc_items):
        """Populate the sidebar TOC widget."""
        # Clear existing items except the title
        self.toc_widget.clear()
        
        # Add title back
        toc_title = QListWidgetItem("📚 Содержание")
        toc_title.setFlags(toc_title.flags() & ~Qt.ItemIsSelectable)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        toc_title.setFont(font)
        toc_title.setBackground(QColor(240, 240, 240))
        self.toc_widget.addItem(toc_title)
        
        if not toc_items:
            item = QListWidgetItem("(Нет заголовков)")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.toc_widget.addItem(item)
            return
        
        for level, text, anchor in toc_items:
            # Create indentation based on heading level
            indent = "    " * (level - 1)
            
            # Add bullet for h1, dash for h2, circle for h3
            if level == 1:
                bullet = "• "
            elif level == 2:
                bullet = "  ◦ "
            else:
                bullet = "    ▪ "
            
            item_text = indent + bullet + text
            item = QListWidgetItem(item_text)
            item.anchor = anchor  # Store anchor as custom attribute
            
            # Apply different font styles based on level
            font = QFont()
            if level == 1:
                font.setBold(True)
                font.setPointSize(10)
            elif level == 2:
                font.setBold(True)
                font.setPointSize(9)
            else:
                font.setPointSize(9)
            
            item.setFont(font)
            self.toc_widget.addItem(item)

    def _load_help(self):
        """Load markdown and convert to styled HTML with sidebar TOC."""

        if not os.path.exists(self.help_file_path):
            self.text_browser.setHtml(
                f"<p style='color:red;'>Файл справки не найден:<br>{self.help_file_path}</p>"
            )
            return

        try:
            with open(self.help_file_path, "r", encoding="utf-8") as f:
                md_text = f.read()

            # Markdown → HTML
            html_raw = markdown.markdown(
                md_text,
                extensions=[
                    "extra",
                    "nl2br",
                ]
            )

            # Extract headings and add anchors
            html_with_anchors, toc_items = self._extract_headings_and_add_anchors(html_raw)
            
            # Fix relative image paths
            html_with_anchors = html_with_anchors.replace("src=\"images/", f"src=\"{self.images_path}/")

            # Final HTML wrapper with clean CSS
            styled_html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 14px;
                        padding: 20px;
                        line-height: 1.45;
                    }}

                    h1, h2, h3 {{
                        margin-top: 1em;
                        margin-bottom: 0.5em;
                        color: #2c3e50;
                        position: relative;
                        padding-top: 10px;
                    }}

                    h1 {{
                        font-size: 1.8em;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 5px;
                    }}

                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #eee;
                        padding-bottom: 3px;
                    }}

                    h3 {{
                        font-size: 1.2em;
                    }}

                    h1:hover::before, h2:hover::before, h3:hover::before {{
                        content: "#";
                        position: absolute;
                        left: -1.2em;
                        color: #ddd;
                        font-size: 0.9em;
                    }}

                    p {{
                        margin: 0.4em 0 0.9em 0;
                    }}

                    /* IMAGES */
                    img {{
                        max-width: 100%;
                        height: auto;
                        display: block;
                        margin: 5px 0 5px 0 !important;
                    }}

                    /* remove markdown-generated <p> spacing around images */
                    p:has(> img) {{
                        margin: 5px 0 !important;
                        padding: 0 !important;
                    }}

                    ul, ol {{
                        margin: 0.3em 0 0.8em 25px;
                    }}

                    li {{
                        margin: 0.2em 0;
                    }}

                    table {{
                        border-collapse: collapse;
                        margin: 0.7em 0;
                        width: 100%;
                    }}

                    th, td {{
                        border: 1px solid #ccc;
                        padding: 6px;
                    }}

                    a {{
                        color: #3498db;
                        text-decoration: none;
                    }}

                    a:hover {{
                        text-decoration: underline;
                    }}

                    hr {{
                        border: none;
                        border-top: 1px solid #ddd;
                        margin: 1.5em 0;
                    }}

                    /* Back to top link */
                    .back-to-top {{
                        display: block;
                        text-align: right;
                        margin-top: 30px;
                        padding-top: 10px;
                        border-top: 1px solid #eee;
                        font-size: 0.9em;
                    }}
                    
                    code {{
                        background-color: #f5f5f5;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                    }}
                    
                    pre {{
                        background-color: #f5f5f5;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                        line-height: 1.4;
                    }}
                </style>
            </head>
            <body>
                {html_with_anchors}
                <div class="back-to-top">
                    <a href="#top">↑ Наверх</a>
                </div>
            </body>
            </html>
            """

            self.text_browser.setHtml(styled_html)
            
            # Populate the sidebar TOC widget
            self._populate_toc_widget(toc_items)

        except Exception as e:
            self.text_browser.setHtml(
                f"<p style='color:red;'>Ошибка загрузки справки:<br>{str(e)}</p>"
            )


def show_help_dialog(parent=None):
    dlg = HelpDialog(parent)
    dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = HelpDialog()
    dlg.show()
    sys.exit(app.exec())