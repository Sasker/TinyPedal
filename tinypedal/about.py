#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2023 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
About window
"""

import logging

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QTabWidget,
)

from .const import APP_NAME, VERSION, APP_ICON, COPYRIGHT, DESCRIPTION, LICENSE, WEBSITE

logger = logging.getLogger(__name__)


class AboutTab(QWidget):
    """About info"""

    def __init__(self):
        super().__init__()

        # Logo
        icon_size = 128
        logo_image = QPixmap(APP_ICON)
        logo_image = logo_image.scaled(icon_size,icon_size, mode=Qt.SmoothTransformation)

        label_logo = QLabel(self)
        label_logo.setPixmap(logo_image)
        label_logo.setFixedSize(icon_size+20,icon_size+20)
        label_logo.setAlignment(Qt.AlignCenter)
        label_logo.setStyleSheet("padding: 10px;")

        # Description
        label_name = QLabel(APP_NAME)
        label_name.setStyleSheet("font-size: 18px;")
        label_name.setAlignment(Qt.AlignCenter)

        label_version = QLabel(f"v{VERSION}\n")
        label_version.setStyleSheet("font-size: 13px;")
        label_version.setAlignment(Qt.AlignCenter)

        label_desc = QLabel(
            f"<p>{COPYRIGHT}</p><p>{DESCRIPTION}</p><p>{LICENSE}</p>"
            f"<p><a href={WEBSITE}>{WEBSITE}</a><br></p>"
        )
        label_desc.setStyleSheet("font-size: 11px;")
        label_desc.setAlignment(Qt.AlignCenter)
        label_desc.setOpenExternalLinks(True)

        # Layout
        layout_logo = QHBoxLayout()
        layout_logo.addWidget(label_logo)
        layout_logo.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        layout_about = QVBoxLayout()
        layout_about.addLayout(layout_logo)
        layout_about.addWidget(label_name)
        layout_about.addWidget(label_version)
        layout_about.addWidget(label_desc)
        layout_about.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(layout_about)


class TextTab(QTextBrowser):
    """Text info"""

    def __init__(self, text):
        super().__init__()
        self.setText(text)
        self.setStyleSheet("font-size: 11px;")
        self.setMinimumSize(400, 300)


class About(QWidget):
    """Create about window

    Hide window at startup.
    """

    def __init__(self, hideonclose=False):
        super().__init__()
        self.hideonclose = hideonclose

        # Base setting
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.setWindowIcon(QIcon(APP_ICON))
        self.setWindowTitle(f"About {APP_NAME}")

        # Tab
        self.main_tab = QTabWidget()
        info_tab = AboutTab()
        ctrb_tab = TextTab(self.load_text_files("docs/contributors.md"))
        lics_tab = TextTab(self.load_text_files("LICENSE.txt"))
        tpan_tab = TextTab(self.load_text_files("docs/licenses/THIRDPARTYNOTICES.txt"))
        self.main_tab.addTab(info_tab, "About")
        self.main_tab.addTab(ctrb_tab, "Contributors")
        self.main_tab.addTab(lics_tab, "License")
        self.main_tab.addTab(tpan_tab, "Third-Party Notices")

        # Button
        button_close = QPushButton("Close")
        button_close.clicked.connect(self.close)

        # Layout
        layout_button = QHBoxLayout()
        layout_button.addStretch(stretch=1)
        layout_button.addWidget(button_close)
        layout_button.setContentsMargins(3,3,7,7)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.main_tab)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(3,3,3,3)
        self.setLayout(layout_main)
        self.setFixedSize(self.sizeHint().width(), self.sizeHint().height())

    @staticmethod
    def load_text_files(filepath):
        """Load text file"""
        try:
            with open(filepath, "r", encoding="utf-8") as text_file:
                return text_file.read()
        except FileNotFoundError:
            logger.error("%s file not found", filepath)
            error_text = "Error: file not found."
            link_text = "See link: https://github.com/s-victor/TinyPedal/blob/master/"
            return f"{error_text} \n{link_text}{filepath}"

    def closeEvent(self, event):
        """Minimize to tray"""
        if self.hideonclose:
            event.ignore()
            self.main_tab.setCurrentIndex(0)
            self.hide()
