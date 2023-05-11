#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2023  Xiang
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
Tyre temperature Widget
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QFont, QFontMetrics
from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
)

from .. import calculation as calc
from .. import validator as val
from .. import readapi as read_data
from ..base import Widget

WIDGET_NAME = "tyre_temperature"


class Draw(Widget):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Widget.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = QFont()
        self.font.setFamily(self.wcfg['font_name'])
        self.font.setPixelSize(self.wcfg['font_size'])
        font_w = QFontMetrics(self.font).averageCharWidth()

        # Config variable
        text_def = "n/a"
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3)
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""

        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            text_width = 4 + len(self.sign_text)
        else:
            text_width = 3 + len(self.sign_text)

        # Base style
        self.heatmap = list(self.load_heatmap().items())

        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
            f"padding: 0 {bar_padx}px;"
        )

        # Create layout
        layout = QGridLayout()
        layout_stemp = QGridLayout()
        layout_itemp = QGridLayout()
        layout_stemp.setSpacing(inner_gap)
        layout_itemp.setSpacing(inner_gap)
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_stemp = self.wcfg["column_index_surface"]
        column_itemp = self.wcfg["column_index_innerlayer"]

        # Tyre temperature
        self.stemp_set = ("stemp_fl", "stemp_fr", "stemp_rl", "stemp_rr")
        self.itemp_set = ("itemp_fl", "itemp_fr", "itemp_rl", "itemp_rr")

        self.bar_width_temp = font_w * text_width
        bar_style_stemp = (
            f"color: {self.wcfg['font_color_surface']};"
            f"background: {self.wcfg['bkg_color_surface']};"
            f"min-width: {self.bar_width_temp}px;"
        )
        bar_style_itemp = (
            f"color: {self.wcfg['font_color_innerlayer']};"
            f"background: {self.wcfg['bkg_color_innerlayer']};"
            f"min-width: {self.bar_width_temp}px;"
        )

        if self.wcfg["show_tyre_compound"]:
            bar_style_tcmpd = (
                f"color: {self.wcfg['font_color_tyre_compound']};"
                f"background: {self.wcfg['bkg_color_tyre_compound']};"
                f"min-width: {font_w}px;"
            )
            self.bar_tcmpd_f = QLabel("-")
            self.bar_tcmpd_f.setAlignment(Qt.AlignCenter)
            self.bar_tcmpd_f.setStyleSheet(bar_style_tcmpd)
            self.bar_tcmpd_r = QLabel("-")
            self.bar_tcmpd_r.setAlignment(Qt.AlignCenter)
            self.bar_tcmpd_r.setStyleSheet(bar_style_tcmpd)
            layout_stemp.addWidget(self.bar_tcmpd_f, 0, 4)
            layout_stemp.addWidget(self.bar_tcmpd_r, 1, 4)

            if self.wcfg["show_innerlayer"]:
                bar_blank_1 = QLabel(" ")
                bar_blank_1.setStyleSheet(bar_style_tcmpd)
                bar_blank_2 = QLabel(" ")
                bar_blank_2.setStyleSheet(bar_style_tcmpd)
                layout_itemp.addWidget(bar_blank_1, 0, 4)
                layout_itemp.addWidget(bar_blank_2, 1, 4)

        if self.wcfg["show_inner_center_outer"]:
            for item in self.stemp_set:
                for idx in range(3):
                    setattr(self, f"bar_{item}_{idx}", QLabel(text_def))
                    getattr(self, f"bar_{item}_{idx}").setAlignment(Qt.AlignCenter)
                    getattr(self, f"bar_{item}_{idx}").setStyleSheet(bar_style_stemp)
                    if item == "stemp_fl":  # 2 1 0
                        layout_stemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 0, 2 - idx)
                    if item == "stemp_fr":  # 7 8 9
                        layout_stemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 0, 7 + idx)
                    if item == "stemp_rl":  # 2 1 0
                        layout_stemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 1, 2 - idx)
                    if item == "stemp_rr":  # 7 8 9
                        layout_stemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 1, 7 + idx)

            if self.wcfg["show_innerlayer"]:
                for item in self.itemp_set:
                    for idx in range(3):
                        setattr(self, f"bar_{item}_{idx}", QLabel(text_def))
                        getattr(self, f"bar_{item}_{idx}").setAlignment(Qt.AlignCenter)
                        getattr(self, f"bar_{item}_{idx}").setStyleSheet(bar_style_itemp)
                        if item == "itemp_fl":  # 2 1 0
                            layout_itemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 0, 2 - idx)
                        if item == "itemp_fr":  # 7 8 9
                            layout_itemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 0, 7 + idx)
                        if item == "itemp_rl":  # 2 1 0
                            layout_itemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 1, 2 - idx)
                        if item == "itemp_rr":  # 7 8 9
                            layout_itemp.addWidget(getattr(self, f"bar_{item}_{idx}"), 1, 7 + idx)

        else:
            for item in self.stemp_set:
                setattr(self, f"bar_{item}", QLabel(text_def))
                getattr(self, f"bar_{item}").setAlignment(Qt.AlignCenter)
                getattr(self, f"bar_{item}").setStyleSheet(bar_style_stemp)
                if item == "stemp_fl":  # 0
                    layout_stemp.addWidget(getattr(self, f"bar_{item}"), 0, 0)
                if item == "stemp_fr":  # 9
                    layout_stemp.addWidget(getattr(self, f"bar_{item}"), 0, 9)
                if item == "stemp_rl":  # 0
                    layout_stemp.addWidget(getattr(self, f"bar_{item}"), 1, 0)
                if item == "stemp_rr":  # 9
                    layout_stemp.addWidget(getattr(self, f"bar_{item}"), 1, 9)

            if self.wcfg["show_innerlayer"]:
                for item in self.itemp_set:
                    setattr(self, f"bar_{item}", QLabel(text_def))
                    getattr(self, f"bar_{item}").setAlignment(Qt.AlignCenter)
                    getattr(self, f"bar_{item}").setStyleSheet(bar_style_itemp)
                    if item == "itemp_fl":  # 0
                        layout_itemp.addWidget(getattr(self, f"bar_{item}"), 0, 0)
                    if item == "itemp_fr":  # 9
                        layout_itemp.addWidget(getattr(self, f"bar_{item}"), 0, 9)
                    if item == "itemp_rl":  # 0
                        layout_itemp.addWidget(getattr(self, f"bar_{item}"), 1, 0)
                    if item == "itemp_rr":  # 9
                        layout_itemp.addWidget(getattr(self, f"bar_{item}"), 1, 9)

        # Set layout
        if self.wcfg["layout"] == 0:
            # Vertical layout
            layout.addLayout(layout_stemp, column_stemp, 0)
            if self.wcfg["show_innerlayer"]:
                layout.addLayout(layout_itemp, column_itemp, 0)
        else:
            # Horizontal layout
            layout.addLayout(layout_stemp, 0, column_stemp)
            if self.wcfg["show_innerlayer"]:
                layout.addLayout(layout_itemp, 0, column_itemp)
        self.setLayout(layout)

        # Last data
        self.last_tcmpd = [None] * 2
        if self.wcfg["show_inner_center_outer"]:
            self.last_stemp = [[-273.15] * 3 for _ in range(4)]
            self.last_itemp = [[-273.15] * 3 for _ in range(4)]
        else:
            self.last_stemp = [-273.15] * 4
            self.last_itemp = [-273.15] * 4

        # Set widget state & start update
        self.set_widget_state()
        self.update_timer.start()

    @Slot()
    def update_data(self):
        """Update when vehicle on track"""
        if self.wcfg["enable"] and read_data.state():

            # Read tyre surface & inner temperature data
            stemp = tuple(map(self.temp_mode, read_data.tyre_temp_surface()))
            tcmpd = self.set_tyre_cmp(read_data.tyre_compound())

            if self.wcfg["show_tyre_compound"]:
                self.update_tcmpd(tcmpd, self.last_tcmpd)
                self.last_tcmpd = tcmpd

            # Inner, center, outer mode
            if self.wcfg["show_inner_center_outer"]:
                # Surface temperature
                for item in self.stemp_set:
                    for idx in range(3):
                        if item == "stemp_fl":  # 2 1 0
                            self.update_stemp(
                                f"{item}_{idx}",
                                stemp[0][2 - idx],
                                self.last_stemp[0][2 - idx]
                            )
                        if item == "stemp_fr":  # 0 1 2
                            self.update_stemp(
                                f"{item}_{idx}",
                                stemp[1][idx],
                                self.last_stemp[1][idx]
                            )
                        if item == "stemp_rl":  # 2 1 0
                            self.update_stemp(
                                f"{item}_{idx}",
                                stemp[2][2 - idx],
                                self.last_stemp[2][2 - idx]
                            )
                        if item == "stemp_rr":  # 0 1 2
                            self.update_stemp(
                                f"{item}_{idx}",
                                stemp[3][idx],
                                self.last_stemp[3][idx]
                            )
                self.last_stemp = stemp

                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = tuple(map(self.temp_mode, read_data.tyre_temp_innerlayer()))
                    for item in self.itemp_set:
                        for idx in range(3):
                            if item == "itemp_fl":  # 2 1 0
                                self.update_itemp(
                                    f"{item}_{idx}",
                                    itemp[0][2 - idx],
                                    self.last_itemp[0][2 - idx]
                                )
                            if item == "itemp_fr":  # 0 1 2
                                self.update_itemp(
                                    f"{item}_{idx}",
                                    itemp[1][idx],
                                    self.last_itemp[1][idx]
                                )
                            if item == "itemp_rl":  # 2 1 0
                                self.update_itemp(
                                    f"{item}_{idx}",
                                    itemp[2][2 - idx],
                                    self.last_itemp[2][2 - idx]
                                )
                            if item == "itemp_rr":  # 0 1 2
                                self.update_itemp(
                                    f"{item}_{idx}",
                                    itemp[3][idx],
                                    self.last_itemp[3][idx]
                                )
                    self.last_itemp = itemp
            # Average mode
            else:
                # Surface temperature
                for idx, item in enumerate(self.stemp_set):
                    self.update_stemp(item, stemp[idx], self.last_stemp[idx])
                self.last_stemp = stemp
                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = tuple(map(self.temp_mode, read_data.tyre_temp_innerlayer()))
                    for idx, item in enumerate(self.itemp_set):
                        self.update_itemp(item, itemp[idx], self.last_itemp[idx])
                    self.last_itemp = itemp

    # GUI update methods
    def update_stemp(self, suffix, curr, last):
        """Tyre surface temperature"""
        if round(curr) != round(last):
            if self.wcfg["swap_style"]:
                color = (f"color: {self.wcfg['font_color_surface']};"
                         f"background: {self.color_heatmap(curr)};")
            else:
                color = (f"color: {self.color_heatmap(curr)};"
                         f"background: {self.wcfg['bkg_color_surface']};")

            sign = "°" if self.wcfg["show_degree_sign"] else ""

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):0{self.leading_zero}.0f}{sign}")

            getattr(self, f"bar_{suffix}").setStyleSheet(
                f"{color}min-width: {self.bar_width_temp}px;")

    def update_itemp(self, suffix, curr, last):
        """Tyre inner temperature"""
        if round(curr) != round(last):
            if self.wcfg["swap_style"]:
                color = (f"color: {self.wcfg['font_color_innerlayer']};"
                         f"background: {self.color_heatmap(curr)};")
            else:
                color = (f"color: {self.color_heatmap(curr)};"
                         f"background: {self.wcfg['bkg_color_innerlayer']};")

            sign = "°" if self.wcfg["show_degree_sign"] else ""

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):0{self.leading_zero}.0f}{sign}")

            getattr(self, f"bar_{suffix}").setStyleSheet(
                f"{color}min-width: {self.bar_width_temp}px;")

    def update_tcmpd(self, curr, last):
        """Tyre compound"""
        if curr != last:
            self.bar_tcmpd_f.setText(curr[0])
            self.bar_tcmpd_r.setText(curr[1])

    # Additional methods
    def temp_mode(self, value):
        """Temperature inner/center/outer mode"""
        if self.wcfg["show_inner_center_outer"]:
            return value
        return sum(value) / 3

    def temp_units(self, value):
        """Temperature units"""
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return calc.celsius2fahrenheit(value)
        return value

    def set_tyre_cmp(self, tc_index):
        """Substitute tyre compound index with custom chars"""
        ftire = self.wcfg["tyre_compound_list"][tc_index[0]:(tc_index[0]+1)]
        rtire = self.wcfg["tyre_compound_list"][tc_index[1]:(tc_index[1]+1)]
        return ftire, rtire

    def load_heatmap(self):
        """Load heatmap dict"""
        if self.wcfg["heatmap_name"] in self.cfg.heatmap_user:
            heatmap = self.cfg.heatmap_user[self.wcfg["heatmap_name"]]
            if val.verify_heatmap(heatmap):
                return heatmap
        return self.cfg.heatmap_default["tyre_default"]

    def color_heatmap(self, temp):
        """Heatmap color"""
        return calc.color_heatmap(self.heatmap, temp)
