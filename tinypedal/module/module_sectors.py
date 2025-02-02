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
Sectors module
"""

import logging
import threading

from ..module_info import minfo
from ..api_control import api
from .. import formatter as fmt
from .. import validator as val

MODULE_NAME = "module_sectors"
MAGIC_NUM = 99999  # magic number for default variable not updated by rF2

logger = logging.getLogger(__name__)


class Realtime:
    """Sectors data"""
    module_name = MODULE_NAME

    def __init__(self, config):
        self.cfg = config
        self.mcfg = self.cfg.setting_user[self.module_name]
        self.stopped = True
        self.event = threading.Event()

    def start(self):
        """Start update thread"""
        if self.stopped:
            self.stopped = False
            self.event.clear()
            _thread = threading.Thread(target=self.__update_data, daemon=True)
            _thread.start()
            self.cfg.active_module_list.append(self)
            logger.info("ACTIVE: module sectors")

    def stop(self):
        """Stop thread"""
        self.event.set()

    def __update_data(self):
        """Update module data"""
        reset = False
        active_interval = self.mcfg["update_interval"] / 1000
        idle_interval = self.mcfg["idle_update_interval"] / 1000
        update_interval = active_interval

        while not self.event.wait(update_interval):
            if api.state:

                if not reset:
                    reset = True
                    update_interval = active_interval

                    last_sector_idx = -1  # previous recorded sector index value
                    combo_id = api.read.check.combo_id()  # current car & track combo
                    session_id = api.read.check.session_id()  # session identity
                    laptime_best, best_s_tb, best_s_pb = self.load_sector_data(
                        combo_id, session_id)
                    delta_s_tb = [0,0,0]  # deltabest times against all time best sector
                    delta_s_pb = [0,0,0]  # deltabest times against best laptime sector
                    prev_s = [MAGIC_NUM,MAGIC_NUM,MAGIC_NUM]  # previous sector times
                    no_delta_s = True

                # Read telemetry
                sector_idx = api.read.lap.sector_index()
                laptime_valid = api.read.timing.last_laptime()
                curr_sector1 = api.read.timing.current_sector1()
                curr_sector2 = api.read.timing.current_sector2()
                last_sector2 = api.read.timing.last_sector2()

                # Update previous & best sector time
                if last_sector_idx != sector_idx:  # keep checking until conditions met

                    # While vehicle in S1, update S3 data
                    if sector_idx == 0 and laptime_valid > 0 and last_sector2 > 0:
                        last_sector_idx = sector_idx  # reset & stop checking

                        prev_s[2] = laptime_valid - last_sector2

                        # Update (time gap) deltabest bestlap sector 3 text
                        if val.sector_time(best_s_pb[2]):
                            delta_s_pb[2] = prev_s[2] - best_s_pb[2] + delta_s_pb[1]

                        # Update deltabest sector 3 text
                        if val.sector_time(best_s_tb[2]):
                            delta_s_tb[2] = prev_s[2] - best_s_tb[2]
                            no_delta_s = False
                        else:
                            no_delta_s = True

                        # Save best sector 3 time
                        if prev_s[2] < best_s_tb[2]:
                            best_s_tb[2] = prev_s[2]

                        # Save sector time from personal best laptime
                        if laptime_valid < laptime_best and val.sector_time(prev_s):
                            laptime_best = laptime_valid
                            best_s_pb = prev_s.copy()

                    # While vehicle in S2, update S1 data
                    elif sector_idx == 1 and curr_sector1 > 0:
                        last_sector_idx = sector_idx  # reset

                        prev_s[0] = curr_sector1

                        # Update (time gap) deltabest bestlap sector 1 text
                        if val.sector_time(best_s_pb[0]):
                            delta_s_pb[0] = prev_s[0] - best_s_pb[0]

                        # Update deltabest sector 1 text
                        if val.sector_time(best_s_tb[0]):
                            delta_s_tb[0] = prev_s[0] - best_s_tb[0]
                            no_delta_s = False
                        else:
                            no_delta_s = True

                        # Save best sector 1 time
                        if prev_s[0] < best_s_tb[0]:
                            best_s_tb[0] = prev_s[0]

                    # While vehicle in S3, update S2 data
                    elif sector_idx == 2 and curr_sector2 > 0 and curr_sector1 > 0:
                        last_sector_idx = sector_idx  # reset

                        prev_s[1] = curr_sector2 - curr_sector1

                        # Update (time gap) deltabest bestlap sector 2 text
                        if val.sector_time(best_s_pb[1]):
                            delta_s_pb[1] = prev_s[1] - best_s_pb[1] + delta_s_pb[0]

                        # Update deltabest sector 2 text
                        if val.sector_time(best_s_tb[1]):
                            delta_s_tb[1] = prev_s[1] - best_s_tb[1]
                            no_delta_s = False
                        else:
                            no_delta_s = True

                        # Save best sector 2 time
                        if prev_s[1] < best_s_tb[1]:
                            best_s_tb[1] = prev_s[1]

                # Output sectors data
                minfo.sectors.sectorIndex = min(max(last_sector_idx, 0), 2)
                minfo.sectors.deltaSectorBestPB = delta_s_pb
                minfo.sectors.deltaSectorBestTB = delta_s_tb
                minfo.sectors.sectorBestTB = best_s_tb
                minfo.sectors.sectorBestPB = best_s_pb
                minfo.sectors.sectorPrev = prev_s
                minfo.sectors.noDeltaSector = no_delta_s

            else:
                if reset:
                    reset = False
                    update_interval = idle_interval
                    # Save only valid sector data
                    self.save_sector_data(
                        combo_id, session_id, best_s_pb, laptime_best, best_s_tb)

        self.cfg.active_module_list.remove(self)
        self.stopped = True
        logger.info("CLOSED: module sectors")

    def save_sector_data(self, combo_id, session_id, best_s_pb, laptime_best, best_s_tb):
        """Verify and save sector data"""
        if session_id and val.sector_time(best_s_pb):
            self.mcfg["sector_info"] = fmt.pipe_join(
                combo_id,      # 0
                *session_id,   # 1 2 3
                laptime_best,  # 4
                *best_s_tb,    # 5 6 7
                *best_s_pb     # 8 9 10
            )
            self.cfg.save()

    def load_sector_data(self, combo_id, session_id):
        """Load and verify sector data

        Check if saved data is from same session, car, track combo, discard if not
        """
        saved_data = self.parse_save_string(self.mcfg["sector_info"])
        if (combo_id == saved_data[0] and
            saved_data[1] == session_id[0] and
            saved_data[2] <= session_id[1] and
            saved_data[3] <= session_id[2]):
            # Assign loaded data
            laptime_best = saved_data[4]  # best laptime (seconds)
            best_s_tb = saved_data[5]     # theory best sector times
            best_s_pb = saved_data[6]     # personal best sector times
        else:
            logger.info("MISSING: sectors data")
            laptime_best = MAGIC_NUM
            best_s_tb = [MAGIC_NUM,MAGIC_NUM,MAGIC_NUM]
            best_s_pb = [MAGIC_NUM,MAGIC_NUM,MAGIC_NUM]
        return laptime_best, best_s_tb, best_s_pb

    def parse_save_string(self, save_data):
        """Parse last saved sector data"""
        string_list = fmt.pipe_split(save_data)
        data = self.convert_value(string_list)

        try:  # fill in data
            final_list = [
                data[0],                    # 0 - combo name, str
                data[1],                    # 1 - session identify, float
                data[2],                    # 2 - session elapsed time, float
                data[3],                    # 3 - session total laps, float
                data[4],                    # 4 - laptime_best, float
                [data[5],data[6],data[7]],  # 5 - best_s_tb, float
                [data[8],data[9],data[10]]  # 6 - best_s_pb, float
            ]
        except IndexError:  # reset data
            final_list = ["None"]

        return final_list

    @staticmethod
    def convert_value(string_list):
        """Convert string list to str, float"""
        return string_list[0], *tuple(map(float, string_list[1:]))
