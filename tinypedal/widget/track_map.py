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
Track map Widget
"""

from PySide2.QtCore import Qt, Slot, QRectF, QLineF
from PySide2.QtGui import QPainterPath, QPainter, QPixmap, QPen, QBrush, QColor

from .. import calculation as calc
from ..api_control import api
from ..base import Widget
from ..module_info import minfo

WIDGET_NAME = "track_map"


class Draw(Widget):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Widget.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"]
        )
        font_m = self.get_font_metrics(self.font)
        self.font_offset = self.calc_font_offset(font_m)

        # Config variable
        self.veh_size = self.wcfg["font_size"] + round(font_m.width * self.wcfg["bar_padding"])

        # Config canvas
        self.area_size = max(self.wcfg["area_size"], 100)
        self.area_margin = min(max(self.wcfg["area_margin"], 0), int(self.area_size/4))
        self.temp_map_size = self.area_size - self.area_margin * 2
        self.resize(self.area_size, self.area_size)

        self.pen = QPen()
        self.brush = QBrush(Qt.SolidPattern)
        self.draw_map_image(self.create_map_path(None))

        # Last data
        self.map_scaled = None
        self.map_range = (0,10,0,10)
        self.map_scale = 1
        self.map_offset = (0,0)

        self.vehicles_data = None
        self.last_coords_hash = -1
        self.last_veh_data_hash = None
        self.circular_map = True

        # Set widget state & start update
        self.set_widget_state()

    @Slot()
    def update_data(self):
        """Update when vehicle on track"""
        if self.wcfg["enable"] and api.state:

            # Map
            coords_hash = minfo.mapping.coordinatesHash
            self.update_map(coords_hash, self.last_coords_hash)
            self.last_coords_hash = coords_hash

            # Vehicles
            veh_data_hash = minfo.vehicles.dataSetHash
            self.update_veh(veh_data_hash, self.last_veh_data_hash)
            self.last_veh_data_hash = veh_data_hash

    # GUI update methods
    def update_map(self, curr, last):
        """Map update"""
        if curr != last:
            self.draw_map_image(
                self.create_map_path(minfo.mapping.coordinates), self.circular_map)

    def update_veh(self, curr, last):
        """Vehicle update"""
        if curr != last:
            self.vehicles_data = minfo.vehicles.dataSet
            self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw map
        painter.drawPixmap(0, 0, self.area_size, self.area_size, self.map_image)

        # Draw vehicles
        if self.vehicles_data:
            self.draw_vehicle(painter)

    def create_map_path(self, raw_coords):
        """Create map path"""
        map_path = QPainterPath()
        if raw_coords:
            dist = calc.distance(raw_coords[0], raw_coords[-1])
            (self.map_scaled, self.map_range, self.map_scale, self.map_offset
             ) = calc.scale_map(raw_coords, self.area_size, self.area_margin)

            for index, coords in enumerate(self.map_scaled):
                if index == 0:
                    map_path.moveTo(*coords)
                else:
                    map_path.lineTo(*coords)

            # Close map loop if start & end distance less than 500 meters
            if dist < 500:
                map_path.closeSubpath()
                self.circular_map = True
            else:
                self.circular_map = False

        # Temp map
        else:
            temp_coords = (
                (self.area_margin, self.area_margin),
                (self.temp_map_size, self.area_margin),
                (self.temp_map_size, self.temp_map_size),
                (self.area_margin, self.temp_map_size)
            )
            (_, self.map_range, self.map_scale, self.map_offset
             ) = calc.scale_map(temp_coords, self.area_size, self.area_margin)

            self.map_scaled = None

            map_path.addEllipse(
                QRectF(
                    self.area_margin,
                    self.area_margin,
                    self.temp_map_size,
                    self.temp_map_size,
                )
            )
            self.circular_map = True
        return map_path

    def draw_map_image(self, map_path, circular_map=True):
        """Draw map image separately"""
        self.map_image = QPixmap(self.area_size, self.area_size)
        self.map_image.fill(Qt.transparent)
        painter = QPainter(self.map_image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        # Draw map outer background
        if self.wcfg["show_background"]:
            painter.fillRect(0, 0, self.area_size, self.area_size, QColor(self.wcfg["bkg_color"]))

        # Draw map inner background
        if self.wcfg["show_map_background"] and circular_map:
            brush = QBrush(Qt.SolidPattern)
            brush.setColor(QColor(self.wcfg["bkg_color_map"]))
            painter.setBrush(brush)
            painter.drawPath(map_path)
            painter.setBrush(Qt.NoBrush)

        # Set pen style
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)

        # Draw map outline
        if self.wcfg["map_outline_width"]:
            pen.setWidth(self.wcfg["map_width"] + self.wcfg["map_outline_width"])
            pen.setColor(QColor(self.wcfg["map_outline_color"]))
            painter.setPen(pen)
            painter.drawPath(map_path)

        # Draw map
        pen.setWidth(self.wcfg["map_width"])
        pen.setColor(QColor(self.wcfg["map_color"]))
        painter.setPen(pen)
        painter.drawPath(map_path)

        # Draw sector
        if self.map_scaled:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(QColor(self.wcfg["start_line_color"]))
                painter.setPen(pen)
                pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                    self.map_scaled[0],  # point a
                    self.map_scaled[1],  # point b
                    1.57079633,  # 90 degree rotation
                    self.wcfg["start_line_length"]
                )
                painter.drawLine(QLineF(pos_x1, pos_y1, pos_x2, pos_y2))

            # Sector lines
            sectors_index = minfo.mapping.sectors
            if self.wcfg["show_sector_line"] and sectors_index and all(sectors_index):
                pen.setWidth(self.wcfg["sector_line_width"])
                pen.setColor(QColor(self.wcfg["sector_line_color"]))
                painter.setPen(pen)

                for idx in range(2):
                    pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                        self.map_scaled[sectors_index[idx]],  # point a
                        self.map_scaled[sectors_index[idx] + 1],  # point b
                        1.57079633,  # 90 degree rotation
                        self.wcfg["sector_line_length"]
                    )
                    painter.drawLine(QLineF(pos_x1, pos_y1, pos_x2, pos_y2))
        else:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(QColor(self.wcfg["start_line_color"]))
                painter.setPen(pen)
                painter.drawLine(
                    QLineF(
                        self.area_margin - self.wcfg["start_line_length"],
                        self.area_size / 2,
                        self.area_margin + self.wcfg["start_line_length"],
                        self.area_size / 2
                    )
                )

    def draw_vehicle(self, painter):
        """Draw vehicles"""
        if self.wcfg["show_vehicle_standings"]:
            painter.setFont(self.font)

        for veh_info in sorted(self.vehicles_data, key=self.sort_vehicles):
            if self.last_coords_hash:
                pos_x, pos_y = self.vehicle_scale(*veh_info.posXZ)
                offset = 0
            else:
                inpit_offset = self.wcfg["font_size"] if veh_info.inPit else 0

                pos_x, pos_y = calc.rotate_pos(
                    6.2831853 * veh_info.percentageDistance,
                    self.temp_map_size / -2 + inpit_offset,  # x pos
                    0  # y pos
                )
                offset = self.area_size / 2

            rect_vehicle = QRectF(
                offset + pos_x - self.veh_size / 2,
                offset + pos_y - self.veh_size / 2,
                self.veh_size,
                self.veh_size
            )

            # Draw circle
            if self.wcfg["vehicle_outline_width"]:
                self.pen.setWidth(self.wcfg["vehicle_outline_width"])
                self.pen.setColor(QColor(self.wcfg["vehicle_outline_color"]))
                painter.setPen(self.pen)
            else:
                painter.setPen(Qt.NoPen)

            self.brush.setColor(
                QColor(
                    self.color_lapdiff(
                        veh_info.isPlayer,
                        veh_info.position,
                        veh_info.inPit,
                        veh_info.isYellow,
                        veh_info.isLapped,
                        veh_info.inGarage,
                    )
                )
            )
            painter.setBrush(self.brush)
            painter.drawEllipse(rect_vehicle)

            # Draw text standings
            if self.wcfg["show_vehicle_standings"]:
                self.pen.setColor(QColor(self.wcfg["font_color"]))
                painter.setPen(self.pen)
                painter.drawText(
                    rect_vehicle.adjusted(0, self.font_offset, 0, 0),
                    Qt.AlignCenter,
                    f"{veh_info.position}"
                )

    # Additional methods
    @staticmethod
    def sort_vehicles(veh_info):
        """Sort vehicle standings for drawing order"""
        return (
            veh_info.isPlayer,
            -veh_info.inGarage,  # reversed
            -veh_info.inPit,     # reversed
            -veh_info.position,  # reversed
        )

    @staticmethod
    def coords_scale(coords, min_range, scale, offset):
        """Coordinates scale & offset"""
        return (coords - min_range) * scale + offset

    def vehicle_scale(self, raw_pos_x, raw_pos_y):
        """Vehicle scale"""
        veh_pos_x = round(
            self.coords_scale(
                raw_pos_x,
                self.map_range[0],  # min range x
                self.map_scale,
                self.map_offset[0]  # offset x
            )
        )
        veh_pos_y = round(
            self.coords_scale(
                raw_pos_y,
                self.map_range[2],  # min range y
                self.map_scale,
                self.map_offset[1]  # offset y
            )
        )
        return veh_pos_x, veh_pos_y

    def color_lapdiff(self, is_player, position, in_pit, is_yellow, is_lapped, in_garage):
        """Compare lap differences & set color"""
        if is_player:
            return self.wcfg["vehicle_color_player"]
        if position == 1:
            return self.wcfg["vehicle_color_leader"]
        if in_pit:
            return self.wcfg["vehicle_color_in_pit"]
        if is_yellow and not in_pit + in_garage:
            return self.wcfg["vehicle_color_yellow"]
        if is_lapped > 0:
            return self.wcfg["vehicle_color_laps_ahead"]
        if is_lapped < 0:
            return self.wcfg["vehicle_color_laps_behind"]
        return self.wcfg["vehicle_color_same_lap"]
