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
Standings Widget
"""

import random

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QFont, QFontMetrics
from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
)

from .. import calculation as calc
from .. import formatter as fmt
from ..api_control import api
from ..base import Widget
from ..module_info import minfo

WIDGET_NAME = "standings"


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
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        self.drv_width = max(int(self.wcfg["driver_name_width"]), 1)
        self.veh_width = max(int(self.wcfg["vehicle_name_width"]), 1)
        self.cls_width = max(int(self.wcfg["class_width"]), 1)
        self.gap_width = max(int(self.wcfg["time_gap_width"]), 1)
        self.int_width = max(int(self.wcfg["time_interval_width"]), 1)
        self.gap_decimals = max(int(self.wcfg["time_gap_decimal_places"]), 0)
        self.int_decimals = max(int(self.wcfg["time_interval_decimal_places"]), 0)

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
            f"padding: 0 {bar_padx}px;"
        )

        # Max display players
        if self.wcfg["enable_multi_class_split_mode"]:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_split_mode"]), 5), 126)
        else:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_combined_mode"]), 5), 126)

        # Empty data set
        self.empty_vehicles_data = (
            0,  # is_player
            (0,0),  # in_pit
            ("",0),  # position
            ("",0),  # driver name
            ("",0),  # vehicle name
            ("",0),  # pos_class
            ("",0),  # veh_class
            (0,0),  # tire_idx
            ("",0),  # laptime
            ("",0),  # time_gap
            (-1,0),  # pit_count
            ("",0),  # time_int
        )

        # Create layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)  # remove border
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(bar_gap)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_pos = self.wcfg["column_index_position"]
        column_drv = self.wcfg["column_index_driver"]
        column_veh = self.wcfg["column_index_vehicle"]
        column_lpt = self.wcfg["column_index_laptime"]
        column_pic = self.wcfg["column_index_position_in_class"]
        column_cls = self.wcfg["column_index_class"]
        column_tcp = self.wcfg["column_index_tyre_compound"]
        column_psc = self.wcfg["column_index_pitstop_count"]
        column_gap = self.wcfg["column_index_timegap"]
        column_int = self.wcfg["column_index_timeinterval"]
        column_pit = self.wcfg["column_index_pitstatus"]

        # Driver position
        if self.wcfg["show_position"]:
            self.bar_width_pos = f"min-width: {font_w * 2}px;"
            bar_style_pos = (
                f"color: {self.wcfg['font_color_position']};"
                f"background: {self.wcfg['bkg_color_position']};"
                f"{self.bar_width_pos}"
            )
            self.generate_bar("pos", bar_style_pos, column_pos)

        # Driver name
        if self.wcfg["show_driver_name"]:
            self.bar_width_drv = f"min-width: {font_w * self.drv_width}px;"
            bar_style_drv = (
                f"color: {self.wcfg['font_color_driver_name']};"
                f"background: {self.wcfg['bkg_color_driver_name']};"
                f"{self.bar_width_drv}"
            )
            self.generate_bar("drv", bar_style_drv, column_drv)

        # Vehicle name
        if self.wcfg["show_vehicle_name"]:
            self.bar_width_veh = f"min-width: {font_w * self.veh_width}px;"
            bar_style_veh = (
                f"color: {self.wcfg['font_color_vehicle_name']};"
                f"background: {self.wcfg['bkg_color_vehicle_name']};"
                f"{self.bar_width_veh}"
            )
            self.generate_bar("veh", bar_style_veh, column_veh)

        # Time gap
        if self.wcfg["show_time_gap"]:
            self.bar_width_gap = f"min-width: {font_w * self.gap_width}px;"
            bar_style_gap = (
                f"color: {self.wcfg['font_color_time_gap']};"
                f"background: {self.wcfg['bkg_color_time_gap']};"
                f"{self.bar_width_gap}"
            )
            self.generate_bar("gap", bar_style_gap, column_gap)

        # Time interval
        if self.wcfg["show_time_interval"]:
            self.bar_width_int = f"min-width: {font_w * self.int_width}px;"
            bar_style_int = (
                f"color: {self.wcfg['font_color_time_interval']};"
                f"background: {self.wcfg['bkg_color_time_interval']};"
                f"{self.bar_width_int}"
            )
            self.generate_bar("int", bar_style_int, column_int)

        # Vehicle laptime
        if self.wcfg["show_laptime"]:
            self.bar_width_lpt = f"min-width: {font_w * 8}px;"
            bar_style_lpt = (
                f"color: {self.wcfg['font_color_laptime']};"
                f"background: {self.wcfg['bkg_color_laptime']};"
                f"{self.bar_width_lpt}"
            )
            self.generate_bar("lpt", bar_style_lpt, column_lpt)

        # Vehicle position in class
        if self.wcfg["show_position_in_class"]:
            self.bar_width_pic = f"min-width: {font_w * 2}px;"
            bar_style_pic = (
                f"color: {self.wcfg['font_color_position_in_class']};"
                f"background: {self.wcfg['bkg_color_position_in_class']};"
                f"{self.bar_width_pic}"
            )
            self.generate_bar("pic", bar_style_pic, column_pic)

        # Vehicle class
        if self.wcfg["show_class"]:
            self.bar_width_cls = f"min-width: {font_w * self.cls_width}px;"
            bar_style_cls = (
                f"color: {self.wcfg['font_color_class']};"
                f"background: {self.wcfg['bkg_color_class']};"
                f"{self.bar_width_cls}"
            )
            self.generate_bar("cls", bar_style_cls, column_cls)

        # Vehicle in pit
        if self.wcfg["show_pit_status"]:
            self.bar_width_pit = f"min-width: {font_w * len(self.wcfg['pit_status_text'])}px;"
            bar_style_pit = (
                f"color: {self.wcfg['font_color_pit']};"
                f"background: {self.wcfg['bkg_color_pit']};"
                f"{self.bar_width_pit}"
            )
            self.generate_bar("pit", bar_style_pit, column_pit)

        # Tyre compound index
        if self.wcfg["show_tyre_compound"]:
            self.bar_width_tcp = f"min-width: {font_w * 2}px;"
            bar_style_tcp = (
                f"color: {self.wcfg['font_color_tyre_compound']};"
                f"background: {self.wcfg['bkg_color_tyre_compound']};"
                f"{self.bar_width_tcp}"
            )
            self.generate_bar("tcp", bar_style_tcp, column_tcp)

        # Pitstop count
        if self.wcfg["show_pitstop_count"]:
            self.bar_width_psc = f"min-width: {font_w * 2}px;"
            bar_style_psc = (
                f"color: {self.wcfg['font_color_pitstop_count']};"
                f"background: {self.wcfg['bkg_color_pitstop_count']};"
                f"{self.bar_width_psc}"
            )
            self.generate_bar("psc", bar_style_psc, column_psc)

        # Set layout
        self.setLayout(self.layout)

        # Start updating
        self.update_data()

        # Set widget state & start update
        self.set_widget_state()
        self.update_timer.start()

    def generate_bar(self, suffix, style, column_idx):
        """Generate data bar"""
        data_slots = len(self.empty_vehicles_data)
        for idx in range(self.veh_range):
            setattr(self, f"row_{idx}_{suffix}", QLabel(""))
            getattr(self, f"row_{idx}_{suffix}").setAlignment(Qt.AlignCenter)
            getattr(self, f"row_{idx}_{suffix}").setStyleSheet(style)
            self.layout.addWidget(
                getattr(self, f"row_{idx}_{suffix}"), idx, column_idx)
            if idx > 0:  # show only first row initially
                getattr(self, f"row_{idx}_{suffix}").setStyleSheet(
                    f"max-height:{self.wcfg['split_gap']}px;"
                )
            # Last data
            setattr(self, f"last_veh_{idx}", [None] * data_slots)

    @Slot()
    def update_data(self):
        """Update when vehicle on track"""
        if self.wcfg["enable"] and api.state and minfo.relative.standings:

            standings_idx = minfo.relative.standings
            vehicles_data = minfo.vehicles.dataSet
            total_idx = len(standings_idx)

            # Standings update
            for idx in range(self.veh_range):

                # Get vehicle data
                if idx < total_idx:
                    setattr(self, f"veh_{idx}",
                            self.get_data(standings_idx[idx], vehicles_data)
                            )
                else:  # bypass index out range
                    setattr(self, f"veh_{idx}",
                            self.empty_vehicles_data
                            )
                # Driver position
                if self.wcfg["show_position"]:
                    self.update_pos(f"{idx}_pos",
                                    getattr(self, f"veh_{idx}")[2],
                                    getattr(self, f"last_veh_{idx}")[2],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Driver name
                if self.wcfg["show_driver_name"]:
                    self.update_drv(f"{idx}_drv",
                                    getattr(self, f"veh_{idx}")[3],
                                    getattr(self, f"last_veh_{idx}")[3],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Vehicle name
                if self.wcfg["show_vehicle_name"]:
                    self.update_veh(f"{idx}_veh",
                                    getattr(self, f"veh_{idx}")[4],
                                    getattr(self, f"last_veh_{idx}")[4],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Time gap
                if self.wcfg["show_time_gap"]:
                    self.update_gap(f"{idx}_gap",
                                    getattr(self, f"veh_{idx}")[9],
                                    getattr(self, f"last_veh_{idx}")[9],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Time interval
                if self.wcfg["show_time_interval"]:
                    self.update_int(f"{idx}_int",
                                    getattr(self, f"veh_{idx}")[11],
                                    getattr(self, f"last_veh_{idx}")[11],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Vehicle laptime
                if self.wcfg["show_laptime"]:
                    self.update_lpt(f"{idx}_lpt",
                                    getattr(self, f"veh_{idx}")[8],
                                    getattr(self, f"last_veh_{idx}")[8],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Vehicle position in class
                if self.wcfg["show_position_in_class"]:
                    self.update_pic(f"{idx}_pic",
                                    getattr(self, f"veh_{idx}")[5],
                                    getattr(self, f"last_veh_{idx}")[5],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Vehicle class
                if self.wcfg["show_class"]:
                    self.update_cls(f"{idx}_cls",
                                    getattr(self, f"veh_{idx}")[6],
                                    getattr(self, f"last_veh_{idx}")[6]
                                    )
                # Vehicle in pit
                if self.wcfg["show_pit_status"]:
                    self.update_pit(f"{idx}_pit",
                                    getattr(self, f"veh_{idx}")[1],
                                    getattr(self, f"last_veh_{idx}")[1]
                                    )
                # Tyre compound index
                if self.wcfg["show_tyre_compound"]:
                    self.update_tcp(f"{idx}_tcp",
                                    getattr(self, f"veh_{idx}")[7],
                                    getattr(self, f"last_veh_{idx}")[7],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Pitstop count
                if self.wcfg["show_pitstop_count"]:
                    self.update_psc(f"{idx}_psc",
                                    getattr(self, f"veh_{idx}")[10],
                                    getattr(self, f"last_veh_{idx}")[10],
                                    getattr(self, f"veh_{idx}")[0]  # is_player
                                    )
                # Store last data reading
                setattr(self, f"last_veh_{idx}", getattr(self, f"veh_{idx}"))

    # GUI update methods
    def update_pos(self, suffix, curr, last, isplayer):
        """Driver position"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_position']};"
                         f"background: {self.wcfg['bkg_color_player_position']};")
            else:
                color = (f"color: {self.wcfg['font_color_position']};"
                         f"background: {self.wcfg['bkg_color_position']};")

            getattr(self, f"row_{suffix}").setText(curr[0])
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_pos}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_drv(self, suffix, curr, last, isplayer):
        """Driver name"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_driver_name']};"
                         f"background: {self.wcfg['bkg_color_player_driver_name']};")
            else:
                color = (f"color: {self.wcfg['font_color_driver_name']};"
                         f"background: {self.wcfg['bkg_color_driver_name']};")

            text = curr[0].upper() if self.wcfg["driver_name_uppercase"] else curr[0]

            getattr(self, f"row_{suffix}").setText(
                text[:self.drv_width].ljust(self.drv_width))
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_drv}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_veh(self, suffix, curr, last, isplayer):
        """Vehicle name"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_vehicle_name']};"
                         f"background: {self.wcfg['bkg_color_player_vehicle_name']};")
            else:
                color = (f"color: {self.wcfg['font_color_vehicle_name']};"
                         f"background: {self.wcfg['bkg_color_vehicle_name']};")

            text = curr[0].upper() if self.wcfg["vehicle_name_uppercase"] else curr[0]

            getattr(self, f"row_{suffix}").setText(
                text[:self.veh_width].ljust(self.veh_width))
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_veh}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_gap(self, suffix, curr, last, isplayer):
        """Time gap"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_time_gap']};"
                         f"background: {self.wcfg['bkg_color_player_time_gap']};")
            else:
                color = (f"color: {self.wcfg['font_color_time_gap']};"
                         f"background: {self.wcfg['bkg_color_time_gap']};")

            getattr(self, f"row_{suffix}").setText(
                fmt.strip_decimal_pt(curr[0][:self.gap_width])
            )
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_gap}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_int(self, suffix, curr, last, isplayer):
        """Time interval"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_time_interval']};"
                         f"background: {self.wcfg['bkg_color_player_time_interval']};")
            else:
                color = (f"color: {self.wcfg['font_color_time_interval']};"
                         f"background: {self.wcfg['bkg_color_time_interval']};")

            getattr(self, f"row_{suffix}").setText(
                fmt.strip_decimal_pt(curr[0][:self.int_width])
            )
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_int}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_lpt(self, suffix, curr, last, isplayer):
        """Vehicle laptime"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_laptime']};"
                         f"background: {self.wcfg['bkg_color_player_laptime']};")
            else:
                color = (f"color: {self.wcfg['font_color_laptime']};"
                         f"background: {self.wcfg['bkg_color_laptime']};")

            getattr(self, f"row_{suffix}").setText(curr[0])
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_lpt}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_pic(self, suffix, curr, last, isplayer):
        """Position in class"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_position_in_class']};"
                         f"background: {self.wcfg['bkg_color_player_position_in_class']};")
            else:
                color = (f"color: {self.wcfg['font_color_position_in_class']};"
                         f"background: {self.wcfg['bkg_color_position_in_class']};")

            getattr(self, f"row_{suffix}").setText(curr[0])
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_pic}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_cls(self, suffix, curr, last):
        """Vehicle class"""
        if curr != last:
            text, bg_color = self.set_class_style(curr[0])
            color = (f"color: {self.wcfg['font_color_class']};"
                     f"background: {bg_color};")

            getattr(self, f"row_{suffix}").setText(text)
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_cls}"
            )
            self.toggle_visibility(curr[0], getattr(self, f"row_{suffix}"))

    def update_pit(self, suffix, curr, last):
        """Vehicle in pit"""
        if curr != last:
            text, bg_color = self.set_pitstatus(curr[0])
            color = (f"color: {self.wcfg['font_color_pit']};"
                     f"background: {bg_color};")

            getattr(self, f"row_{suffix}").setText(text)
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_pit}"
            )
            self.toggle_visibility(text, getattr(self, f"row_{suffix}"))

    def update_tcp(self, suffix, curr, last, isplayer):
        """Tyre compound index"""
        if curr != last:
            if self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_tyre_compound']};"
                         f"background: {self.wcfg['bkg_color_player_tyre_compound']};")
            else:
                color = (f"color: {self.wcfg['font_color_tyre_compound']};"
                         f"background: {self.wcfg['bkg_color_tyre_compound']};")

            text = self.set_tyre_cmp(curr[0])
            getattr(self, f"row_{suffix}").setText(text)
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_tcp}"
            )
            self.toggle_visibility(text, getattr(self, f"row_{suffix}"))

    def update_psc(self, suffix, curr, last, isplayer):
        """Pitstop count"""
        if curr != last:
            if self.wcfg["show_pit_request"] and curr[1] == 1:
                color = (f"color: {self.wcfg['font_color_pit_request']};"
                         f"background: {self.wcfg['bkg_color_pit_request']};")
            elif self.wcfg["show_player_highlighted"] and isplayer:
                color = (f"color: {self.wcfg['font_color_player_pitstop_count']};"
                         f"background: {self.wcfg['bkg_color_player_pitstop_count']};")
            else:
                color = (f"color: {self.wcfg['font_color_pitstop_count']};"
                         f"background: {self.wcfg['bkg_color_pitstop_count']};")

            text = self.set_pitcount(curr[0])
            getattr(self, f"row_{suffix}").setText(text)
            getattr(self, f"row_{suffix}").setStyleSheet(
                f"{color}{self.bar_width_psc}"
            )
            self.toggle_visibility(text, getattr(self, f"row_{suffix}"))

    # Additional methods
    def toggle_visibility(self, state, row_bar):
        """Hide row bar if empty data"""
        if self.wcfg["split_gap"] > 0:
            if not state:  # add gap between non-empty data
                row_bar.setStyleSheet(f"max-height:{self.wcfg['split_gap']}px;")
        else:  # workaround to 1px minimum bar height limit
            if state:
                if row_bar.isHidden():
                    row_bar.show()
            else:
                if not row_bar.isHidden():
                    row_bar.hide()

    def set_tyre_cmp(self, tc_index):
        """Substitute tyre compound index with custom chars"""
        if tc_index:
            ftire = self.wcfg["tyre_compound_list"][tc_index[0]:(tc_index[0]+1)]
            rtire = self.wcfg["tyre_compound_list"][tc_index[1]:(tc_index[1]+1)]
            return f"{ftire}{rtire}"
        return ""

    def set_pitstatus(self, pits):
        """Set pit status color"""
        if pits > 0:
            return self.wcfg["pit_status_text"], self.wcfg["bkg_color_pit"]
        return "", "#00000000"

    @staticmethod
    def set_pitcount(pits):
        """Set pitstop count test"""
        if pits == 0:
            return "-"
        if pits > 0:
            return f"{pits}"
        return ""

    def set_class_style(self, vehclass_name):
        """Compare vehicle class name with user defined dictionary"""
        if not vehclass_name:
            return "", self.wcfg["bkg_color_class"]

        for full_name, short_name in self.cfg.classes_user.items():
            if vehclass_name == full_name:
                for sub_name, sub_color in short_name.items():
                    return sub_name[:self.cls_width], sub_color

        if self.wcfg["show_random_color_for_unknown_class"]:
            random.seed(vehclass_name)
            rgb = [30,180,random.randrange(30,180)]
            random.shuffle(rgb)
            color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        else:
            color = self.wcfg["bkg_color_class"]
        return vehclass_name[:self.cls_width], color

    @staticmethod
    def set_laptime(inpit, laptime_last, pit_time):
        """Set lap time"""
        if inpit:
            return "PIT" + f"{pit_time:.01f}"[:5].rjust(5) if pit_time > 0 else "-:--.---"
        if laptime_last <= 0:
            return "OUT" + f"{pit_time:.01f}"[:5].rjust(5) if pit_time > 0 else "-:--.---"
        return calc.sec2laptime_full(laptime_last)[:8].rjust(8)

    def gap_to_leader_race(self, time_behind, laps_behind, position):
        """Gap to race leader"""
        if position == 1:
            return self.wcfg["time_gap_leader_text"]
        if time_behind == 0 and laps_behind > 0:
            return f"{laps_behind:.0f}L"
        return f"{time_behind:.0{self.gap_decimals}f}"

    def gap_to_session_bestlap(self, bestlap, sbestlap, cbestlap):
        """Gap to session best laptime"""
        if self.wcfg["show_time_gap_from_class_best"]:
            time = bestlap - cbestlap  # class best
        else:
            time = bestlap - sbestlap  # session best
        if time == 0 and bestlap > 0:
            return self.wcfg["time_gap_leader_text"]
        if time < 0 or bestlap < 1:  # no time set
            return "0.0"
        return f"{time:.0{self.gap_decimals}f}"

    def int_to_next(self, time_behind, laps_behind, position):
        """Interval to next"""
        if position == 1:
            return self.wcfg["time_interval_leader_text"]
        if time_behind == 0 and laps_behind > 0:
            return f"{laps_behind:.0f}L"
        return f"{time_behind:.0{self.int_decimals}f}"

    def get_data(self, index, vehicles_data):
        """Standings data"""
        # Prevent index out of range
        if vehicles_data and 0 <= index < len(vehicles_data):
            # 0 Is player
            is_player = vehicles_data[index].isPlayer

            # 1 Vehicle in pit
            in_pit = (vehicles_data[index].inPit, is_player)

            # 2 Driver position
            position = (f"{vehicles_data[index].position:02d}", is_player)

            # 3 Driver name
            drv_name = (vehicles_data[index].driverName, is_player)

            # 4 Vehicle name
            veh_name = (vehicles_data[index].vehicleName, is_player)

            # 5 Vehicle position in class
            pos_class = (f"{vehicles_data[index].positionInClass:02d}", is_player)

            # 6 Vehicle class
            veh_class = (vehicles_data[index].vehicleClass, is_player)

            # 7 Tyre compound index
            tire_idx = (vehicles_data[index].tireCompoundIndex, is_player)

            if api.read.state.in_race():
                # 8 Lap time
                laptime = (
                    self.set_laptime(
                        vehicles_data[index].inPit,
                        vehicles_data[index].lastLapTime,
                        vehicles_data[index].pitTime
                    ),
                    is_player)
                # 9 Time gap
                time_gap = (
                    self.gap_to_leader_race(
                        vehicles_data[index].timeBehindLeader,
                        vehicles_data[index].lapsBehindLeader,
                        vehicles_data[index].position
                    ),
                    is_player)
            else:
                laptime = (
                    self.set_laptime(
                        0,
                        vehicles_data[index].bestLapTime,
                        0
                    ),
                    is_player)
                time_gap = (
                    self.gap_to_session_bestlap(
                        vehicles_data[index].bestLapTime,
                        vehicles_data[index].sessionBestLapTime,
                        vehicles_data[index].classBestLapTime,
                    ),
                    is_player)

            # 10 Pitstop count
            pit_count = (vehicles_data[index].numPitStops,
                         vehicles_data[index].pitState,
                         is_player)

            # 11 Time interval
            time_int = (
                self.int_to_next(
                    vehicles_data[index].timeBehindNext,
                    vehicles_data[index].lapsBehindNext,
                    vehicles_data[index].position
                ),
                is_player)

            return (is_player, in_pit, position, drv_name, veh_name, pos_class, veh_class,
                    tire_idx, laptime, time_gap, pit_count, time_int)
        # Assign empty value to -1 index
        return self.empty_vehicles_data
