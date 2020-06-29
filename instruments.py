import re
import io
import time
import struct
from decimal import Decimal

from PIL import Image

import vxi11

class DS1000Z(vxi11.Instrument):
    """
    This class represents the oscilloscope.
    """

    def __init__(self, host, *args, **kwargs):
        super(DS1000Z, self).__init__(host, *args, **kwargs)
        idn = self.get_identification()
        match = re.match(r"^RIGOL TECHNOLOGIES,DS1\d\d\dZ( Plus)?,", idn)
        if not match:
            msg = (
                "Unknown device identification:\n%s\n"
                "If you believe this device should be supported "
                "by this package, feel free to contact "
                "the maintainer with this information." % idn
            )
            raise NameError(msg)

    def __str__(self):
        return self.get_identification()

    def _interpret_channel(self, channel):
        """
        Wrapper to allow specifying channels by their name (str) or by their
        number (int)
        """
        if type(channel) == int:
            assert channel <= 4 and channel >= 1
            channel = "CHAN" + str(channel)
        return channel

    def _interpret_source(self, source):
        """
        Wrapper to allow specifying sources by their name (str) or by their
        number (int)
        """
        if type(source) == int:
            assert source <= 2 and source >= 1
            source = "SOUR" + str(source)
        return source

    def _interpret_reference(self, reference):
        """
        Wrapper to allow specifying references by their name (str) or by their
        number (int)
        """
        if type(reference) == int:
            assert reference <= 10 and reference >= 1
            reference = "REF" + str(reference)
        return reference

    def _interpret_item(self, item):
        """
        Wrapper to allow specifying items by their name (str) or by their number
        (int)
        """
        if type(item) == int:
            assert item <= 5 and item >= 1
            item = "ITEM" + str(item)
        return item

    def _masked_float(self, number):
        number = float(number)
        if number == 9.9e37:
            return None
        else:
            return number

    def autoscale(self):
        """
        Enable the waveform auto setting function. The oscilloscope will
        automatically adjust the vertical scale, horizontal timebase and trigger
        mode according to the input signal to realize optimum wave display. This
        command is equivalent to pressing the AUTO key at the front panel.
        """
        assert not self.mask_is_enabled()
        self.write(":AUT")

    def clear(self):
        """
        Clear all the waveforms on the screen. If the oscilloscope is in the RUN
        state, waveform will still be displayed. This command is equivalent to
        pressing the CLEAR key at the front panel.
        """
        self.write(":CLE")

    def run(self):
        """
        Make the oscilloscope start running. equivalent to pressing the RUN/STOP
        key at the front panel.
        """
        self.write(":RUN")

    def stop(self):
        """
        Make the oscilloscope stop running. equivalent to pressing the RUN/STOP
        key at the front panel.
        """
        self.write(":STOP")

    def get_averages(self):
        """
        Query the number of averages under the average acquisition mode.
        """
        return int(self.ask(":ACQ:AVER?"))

    def set_averages(self, count=2):
        """
        Set the number of averages under the average acquisition mode.
        """
        possible_counts = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        count = min(possible_counts, key=lambda x: abs(x - count))
        self.write(":ACQ:AVER {0}".format(count))

    def get_memory_depth(self):
        """
        Query the memory depth of the oscilloscope namely the number of waveform
        points that can be stored in a single trigger sample. The default unit
        is pts (points).
        """
        response = self.ask(":ACQuire:MDEPth?")
        if response == "AUTO":
            return response
        else:
            return int(response)

    def set_memory_depth(self, memory_depth="AUTO"):
        """
        Query the memory depth of the oscilloscope namely the number of waveform
        points that can be stored in a single trigger sample. The default unit
        is pts (points).
        """
        assert self.is_running()
        if type(memory_depth) in (float, int):
            num_channels_shown = self.num_channels_shown()
            if num_channels_shown <= 1:
                possible_memory_depths = [12000, 120000, 1200000, 12000000]
            elif num_channels_shown <= 2:
                possible_memory_depths = [6000, 60000, 600000, 6000000]
            else:
                possible_memory_depths = [3000, 30000, 300000, 3000000]
            memory_depth = min(
                possible_memory_depths, key=lambda x: abs(x - memory_depth)
            )
        elif memory_depth == "AUTO":
            pass
        else:
            raise ValueError
        self.write(":ACQuire:MDEPth {0}".format(memory_depth))

    def get_acquisition_type(self):
        """
        Query the acquisition mode when the oscilloscope samples.
        """
        return self.ask(":ACQ:TYPE?")

    def set_acquisition_type(self, type="NORM"):
        """
        Set the acquisition mode when the oscilloscope samples.
        """
        assert type in ["NORM", "AVER", "PEAK", "HRES"]
        self.write(":ACQ:TYPE {0}".format(type))

    def get_sample_rate(self):
        """
        Query the current sample rate. The default unit is Sa/s.
        """
        return self._masked_float(self.ask(":ACQuire:SRATe?"))

    def start_calibration(self):
        """
        The oscilloscope starts to execute the self-calibration.
        """
        return self.write("CAL:STAR")

    def quit_calibration(self):
        """
        Exit the calibration at any time.
        """
        return self.write("CAL:QUIT")

    def get_bandwidth_limit(self, channel=1):
        """
        Get the bandwidth limit parameter of the specified channel.
        """
        channel = self._interpret_channel(channel)
        return self.ask(":{0}:BWL?".format(channel))

    def set_bandwidth_limit(self, type="OFF", channel=1):
        """
        Set the bandwidth limit parameter of the specified channel.
        """
        channel = self._interpret_channel(channel)
        assert type in ["20M", "OFF"]
        self.write(":{0}:BWL {1}".format(channel, type))

    def get_channel_coupling(self, channel=1):
        """
        Get the coupling mode of the specified channel.
        """
        channel = self._interpret_channel(channel)
        return self.ask(":{0}:COUP?".format(channel))

    def set_channel_coupling(self, coupling="DC", channel=1):
        """
        Set the coupling mode of the specified channel.
        """
        channel = self._interpret_channel(channel)
        assert coupling in ["AC", "DC", "GND"]
        self.write(":{0}:COUP {1}".format(channel, coupling))

    def channel_is_shown(self, channel=1):
        """
        Query the status of the specified channel.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            return self.math_is_shown()
        else:
            return bool(int(self.ask(":{0}:DISP?".format(channel))))

    def show_channel(self, channel=1):
        """
        Enable the specified channel.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            return self.show_math()
        else:
            self.write(":{0}:DISP 1".format(channel))

    def hide_channel(self, channel=1):
        """
        Disable the specified channel.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            return self.hide_math()
        else:
            self.write(":{0}:DISP 0".format(channel))

    def num_channels_shown(self):
        return sum([int(self.channel_is_shown(channel)) for channel in range(1, 5)])

    def channel_is_inverted(self, channel=1):
        """
        Query the status of the inverted display mode of the specified channel.
        """
        channel = self._interpret_channel(channel)
        return bool(int(self.ask(":{0}:INV?".format(channel))))

    def invert_channel(self, channel=1):
        """
        Enable or disable the inverted display mode of the specified channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":{0}:INV 1".format(channel))

    def uninvert_channel(self, channel=1):
        """
        Enable or disable the inverted display mode of the specified channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":{0}:INV 0".format(channel))

    def get_channel_offset(self, channel=1):
        """
        Query the vertical offset of the specified channel. The default unit is
        V.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            return self.get_math_offset()
        else:
            return self._masked_float(self.ask(":{0}:OFFSet?".format(channel)))

    def set_channel_offset(self, offset=0, channel=1):
        """
        Set the vertical offset of the specified channel. The default unit is V.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            self.set_math_offset(offset)
        else:
            if self.get_channel_scale() >= 0.5:
                assert abs(offset) <= self.get_probe_ratio() * 100
            else:
                assert abs(offset) <= self.get_probe_ratio() * 2
            self.write(":{0}:OFFSet {1}".format(channel, offset))

    def get_channel_range(self, channel=1):
        """
        Query the vertical range of the specified channel. The default unit is
        V.
        """
        channel = self._interpret_channel(channel)
        return self._masked_float(self.ask(":{0}:RANG?".format(channel)))

    def set_channel_range(self, range=8, channel=1):
        """
        Set the vertical range of the specified channel. The default unit is V.
        """
        channel = self._interpret_channel(channel)
        possible_ranges = [
            val ** self.get_probe_ratio()
            for val in [0.008, 0.016, 0.04, 0.08, 0.16, 0.4, 0.8, 1.6, 4, 8, 16, 40, 80]
        ]
        range = min(possible_ranges, key=lambda x: abs(x - range))
        self.write(":{0}:RANG {1}".format(channel, range))

    def get_calibration_time(self, channel=1):
        """
        Query the delay calibration time of the specified channel to calibrate
        the zero offset of the corresponding channel. The default unit is s.
        """
        channel = self._interpret_channel(channel)
        return self._masked_float(self.ask(":{0}:TCAL?".format(channel)))

    def set_calibration_time(self, t=0, channel=1):
        """
        Set the delay calibration time of the specified channel to calibrate the
        zero offset of the corresponding channel. The default unit is s.
        """
        channel = self._interpret_channel(channel)
        timebase_scale = self.get_timebase_scale()
        possible_times = [
            round(x * timebase_scale / 50, 10)
            for x in range(
                int(-1 / (2e5 * timebase_scale)), int(1 / (2e5 * timebase_scale) + 1)
            )
        ]
        t = min(possible_times, key=lambda x: abs(x - t))
        self.write(":{0}:TCAL {1}".format(channel, t))

    def get_channel_scale(self, channel=1):
        """
        Query the vertical scale of the specified channel. The default unit is
        V.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            return self.get_math_scale()
        else:
            return self._masked_float(self.ask(":{0}:SCALe?".format(channel)))

    def set_channel_scale(self, scale=1, channel=1):
        """
        Set the vertical scale of the specified channel. The default unit is V.
        """
        channel = self._interpret_channel(channel)
        if channel == "MATH":
            self.set_math_scale(scale)
        else:
            possible_scales = [
                val * self.get_probe_ratio(channel)
                for val in [1e-3, 2e-3, 5e-3, 1, 2, 5, 1e1, 2e1, 5e1]
            ]
            scale = min(possible_scales, key=lambda x: abs(x - scale))
            self.write(":{0}:SCALe {1}".format(channel, scale))

    def get_probe_ratio(self, channel=1):
        """
        Query the probe ratio of the specified channel.
        """
        channel = self._interpret_channel(channel)
        return self._masked_float(self.ask(":{0}:PROBe?".format(channel)))

    def set_probe_ratio(self, probe_ratio=10, channel=1):
        """
        Set the probe ratio of the specified channel.
        """
        channel = self._interpret_channel(channel)
        probe_ratios = [
            0.01,
            0.02,
            0.05,
            0.1,
            0.2,
            0.5,
            1,
            2,
            5,
            10,
            20,
            50,
            100,
            200,
            500,
            1000,
        ]
        probe_ratio = min(probe_ratios, key=lambda x: abs(x - probe_ratio))
        self.write(":{0}:PROBe {1}".format(channel, probe_ratio))

    def get_channel_unit(self, channel=1):
        """
        Query the amplitude display unit of the specified channel.
        """
        channel = self._interpret_channel(channel)
        return self.ask(":{0}:UNIT?".format(channel))

    def set_channel_unit(self, unit="VOLT", channel=1):
        """
        Set the amplitude display unit of the specified channel.
        """
        channel = self._interpret_channel(channel)
        assert unit in ["VOLT", "WATT", "AMP", "UNKN"]
        self.write(":{0}:UNIT {1}".format(channel, unit))

    def vernier_is_enabled(self, channel=1):
        """
        Query the fine adjustment status of the vertical scale of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        return bool(int(self.ask(":{0}:VERN?".format(channel))))

    def enable_vernier(self, channel=1):
        """
        Enable the fine adjustment of the vertical scale of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":{0}:VERN 1".format(channel))

    def disable_vernier(self, channel=1):
        """
        Disable the fine adjustment of the vertical scale of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":{0}:VERN 0".format(channel))

    def get_cursor_mode(self):
        """
        Query the cursor measurement mode.
        """
        return self.ask(":CURS:MODE?")

    def set_cursor_mode(self, mode="OFF"):
        """
        Set the cursor measurement mode.
        """
        assert mode in ["OFF", "MAN", "TRAC", "AUTO", "XY"]
        if mode == "XY":
            assert self.get_timebase_mode() == "XY"
        self.write(":CURS:MODE {0}".format(mode))

    def get_cursor_type(self):
        """
        Query the cursor type in manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        return self.ask(":CURS:{0}:TYPE?".format(cursor_mode))

    def set_cursor_type(self, type="X"):
        """
        Set the cursor type in manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        assert type in ["X", "Y"]
        self.write(":CURS:{0}:TYPE {1}".format(cursor_mode, type))

    def get_cursor_source(self, source=None):
        """
        Query the channel source of the cursor.
        """
        cursor_mode = self.get_cursor_mode()
        if cursor_mode == "MAN":
            return self.ask(":CURS:{0}:SOUR?".format(cursor_mode))
        elif cursor_mode == "TRAC":
            assert source is not None
            source = self._interpret_source(source)
            return self.ask(":CURS:{0}:{1}?".format(cursor_mode, source))

    def set_cursor_source(self, channel=1, source=None):
        """
        Set the channel source of the cursor.
        """
        channel = self._interpret_channel(channel)
        assert channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH"]
        assert self.channel_is_shown(channel)
        cursor_mode = self.get_cursor_mode()
        if cursor_mode == "MAN":
            self.write(":CURS:{0}:SOUR {1}".format(cursor_mode, channel))
        elif cursor_mode == "TRAC":
            assert source is not None
            source = self._interpret_source(source)
            self.write(":CURS:{0}:{1} {2}".format(cursor_mode, source, channel))
        else:
            raise ValueError

    def get_cursor_time_unit(self):
        """
        Query the horizontal unit in the manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        return self.ask(":CURS:{0}:TUN?".format(cursor_mode))

    def set_cursor_time_unit(self, unit="S"):
        """
        Set the horizontal unit in the manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        assert unit in ["S", "HZ", "DEGR", "PERC"]
        self.write(":CURS:{0}:TUN {1}".format(cursor_mode, unit))

    def get_cursor_vertical_unit(self):
        """
        Query the vertical unit in the manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        return self.ask(":CURS:{0}:VUN?".format(cursor_mode))

    def set_cursor_vertical_unit(self, unit="SOUR"):
        """
        Set the vertical unit in the manual cursor measurement mode.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN"]
        assert unit in ["PERC", "SOUR"]
        self.write(":CURS:{0}:VUN {1}".format(cursor_mode, unit))

    def get_cursor_position(self, cursor="A", axis="X"):
        """
        Query the position of a cursor.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN", "TRAC", "XY"]
        assert cursor in ["A", "B"]
        assert axis in ["X", "Y"]
        return int(self.ask(":CURS:{0}:{1}{2}?".format(cursor_mode, cursor, axis)))

    def set_cursor_position(self, cursor="A", axis="X", position=None):
        """
        Set the position of a cursor.
        """

        # Input checks
        assert cursor in ["A", "B"]
        assert axis in ["X", "Y"]
        if position is None:
            default_positions = {"A": {"X": 100, "Y": 100}, "B": {"X": 500, "Y": 300}}
            position = default_positions[cursor][axis]

        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN", "TRAC", "XY"]
        if cursor_mode == "TRAC" and axis == "Y":
            raise ValueError
        possible_positions = {"X": range(5, 595), "Y": range(5, 395)}
        position = min(possible_positions[axis], key=lambda x: abs(x - position))
        self.write(":CURS:{0}:{1}{2} {3}".format(cursor_mode, cursor, axis, position))

    def get_cursor_value(self, cursor="A", axis="X"):
        """
        Query the value of a cursor. The unit depends on the unit currently
        selected.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN", "TRAC", "XY"]
        assert cursor in ["A", "B"]
        assert axis in ["X", "Y"]
        return self._masked_float(
            self.ask(":CURS:{0}:{1}{2}Value?".format(cursor_mode, cursor, axis))
        )

    def get_cursor_delta(self, axis="X"):
        """
        Query the difference between the values of cursor A and cursor B. The
        unit depends on the unit currently selected.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN", "TRAC"]
        assert axis in ["X", "Y"]
        return self._masked_float(
            self.ask(":CURS:{0}:{1}DEL?".format(cursor_mode, axis))
        )

    def get_cursor_inverse_delta(self):
        """
        Query the reciprocal of the absolute value of the difference between the
        values of cursor A and cursor B. The unit depends on the unit currently
        selected.
        """
        cursor_mode = self.get_cursor_mode()
        assert cursor_mode in ["MAN", "TRAC"]
        return self._masked_float(self.ask(":CURS:{0}:IXDELta?".format(cursor_mode)))

    def get_cursor_auto_parameters(self):
        """
        Query the parameters currently measured by the auto cursor.
        """
        parameters = self.ask(":CURS:AUTO:ITEM?")
        assert parameters in ["ITEM1", "ITEM2", "ITEM3", "ITEM4", "ITEM5"]
        return parameters

    def set_cursor_auto_parameters(self, parameters="OFF"):
        """
        The auto cursor function can measure 24 waveform parameters. Using this
        command, you can select the parameters to be measured by the auto cursor
        from the five parameters enabled last.
        """
        assert parameters in ["OFF", "ITEM1", "ITEM2", "ITEM3", "ITEM4", "ITEM5"]
        self.write(":CURS:AUTO:ITEM {0}".format(parameters))

    def take_screenshot(self):
        """
        Read the bitmap data stream of the image currently displayed.
        """
        self.write(":DISPlay:DATA? ON,OFF,PNG")
        buff = self.read_raw(100000)
        n_header_bytes = int(chr(buff[1])) + 2
        n_data_bytes = int(buff[2:n_header_bytes].decode("ascii"))
        decoded_block = buff[n_header_bytes : n_header_bytes + n_data_bytes]
        im = Image.open(io.BytesIO(decoded_block))
        filename = time.strftime("%Y-%m-%d_%H-%M-%S.png", time.localtime())
        im.save(filename, format="png")
        return filename

    def get_display_type(self):
        """
        Query the display mode of the waveform on the screen.
        """
        return self.ask(":DISP:TYPE?")

    def set_display_type(self, type="VECT"):
        """
        Set the display mode of the waveform on the screen.
        """
        assert type in ["VECT", "DOTS"]
        self.write(":DISP:TYPE {0}".format(type))

    def get_persistence_time(self):
        """
        Query the persistence time. The default unit is s.
        """
        persistence_time = self.ask(":DISP:GRAD:TIME?")
        if persistence_time in ["MIN", "INF"]:
            return persistence_time
        else:
            return self._masked_float(persistence_time)

    def set_persistence_time(self, persistence_time="MIN"):
        """
        Set the persistence time. The default unit is s.
        """
        if type(persistence_time) in (float, int):
            persistence_time = min(
                [0.1, 0.2, 0.5, 1, 5, 10], key=lambda x: abs(x - persistence_time)
            )
        assert persistence_time in ["MIN", 0.1, 0.2, 0.5, 1, 5, 10, "INF"]
        self.write(":DISP:GRAD:TIME {0}".format(persistence_time))

    def get_waveform_brightness(self):
        """
        Query the waveform brightness. The default unit is %.
        """
        return int(self.ask(":DISP:WBR?"))

    def set_waveform_brightness(self, brightness=50):
        """
        Set the waveform brightness. The default unit is %.
        """
        assert brightness >= 0 and brightness <= 100
        self.write(":DISP:WBR {0}".format(brightness))

    def get_grid(self):
        """
        Query the grid type of screen display.
        """
        return self.ask(":DISPlay:GRID?")

    def set_grid(self, grid="FULL"):
        """
        Set the grid type of screen display.
        """
        assert grid in ["FULL", "HALF", "NONE"]
        self.write(":DISP:GRID {0}".format(grid))

    def get_grid_brightness(self):
        """
        Query the brightness of the screen grid. The default unit is %.
        """
        return int(self.ask(":DISP:GBR?"))

    def set_grid_brightness(self, brightness=50):
        """
        Set the brightness of the screen grid. The default unit is %.
        """
        assert brightness >= 0 and brightness <= 100
        self.write(":DISP:GBR {0}".format(brightness))

    def clear_status(self):
        """
        Clear all the event registers in the register set and clear the error
        queue.
        """
        self.write("*CLS")

    def get_event_status_enable(self):
        """
        Query the enable register for the standard event status register set.
        """
        return int(self.ask("*ESE?"))

    def set_event_status_enable(self, data=0):
        """
        Set the enable register for the standard event status register set.
        """
        assert data >= 0 and data <= 255
        self.write("*ESE {0}".format(data))

    def get_event_status(self):
        """
        Query and clear the event register for the standard event status
        register.
        """
        return int(self.ask("*ESR?"))

    def get_identification(self):
        """
        Query the ID string of the instrument.
        """
        return self.ask("*IDN?")

    def get_vendor(self):
        return self.get_identification().split(",")[0]

    def get_product(self):
        return self.get_identification().split(",")[1]

    def get_serial_number(self):
        return self.get_identification().split(",")[2]

    def get_firmware(self):
        return self.get_identification().split(",")[3]

    def is_busy(self):
        """
        The *OPC? command is used to query whether the current operation is
        finished. The *OPC command is used to set the Operation Complete bit
        (bit 0) in the standard event status register to 1 after the current
        operation is finished.
        """
        return not bool(int(self.ask("*OPC?")))

    def reset(self):
        """
        Restore the instrument to the default state.
        """
        self.write("*RST")

    def get_service_request_enable(self):
        """
        Query the enable register for the status byte register set.
        """
        return int(self.ask("*SRE?"))

    def set_service_request_enable(self, data=0):
        """
        Set the enable register for the status byte register set.
        """
        assert data >= 0 and data <= 255
        self.write("*SRE {0}".format(data))

    def get_status_byte(self):
        """
        Query the event regester for the status byte register. The
        value of the status byte register is set to 0 after this
        command is executed.
        """
        return int(self.ask("*STB?"))

    def self_test_is_passing(self):
        """
        Perform a self-test and then returns the self-test results.
        """
        return not bool(int(self.ask("*TST?")))

    def wait(self):
        """
        Wait for the operation to finish.
        """
        self.write("*WAI")

    def math_is_shown(self):
        """
        Query the math operation status.
        """
        return bool(int(self.ask(":MATH:DISP?")))

    def show_math(self):
        """
        Enable the math operation function.
        """
        self.write(":MATH:DISP 1")

    def hide_math(self):
        """
        Disable the math operation function.
        """
        self.write(":MATH:DISP 0")

    def get_math_operator(self):
        """
        Query the operator of the math operation.
        """
        return self.ask(":MATH:OPER?")

    def set_math_operator(self, operator="ADD"):
        """
        Set the operator of the math operation.
        """
        assert operator in [
            "ADD",
            "SUBT",
            "MULT",
            "DIV",
            "AND",
            "OR",
            "XOR",
            "NOT",
            "FFT",
            "INTG",
            "DIFF",
            "SQRT",
            "LOG",
            "LN",
            "EXP",
            "ABS",
        ]
        self.write(":MATH:OPER {0}".format(operator))

    def get_math_source(self, source=1):
        """
        Query the source of the math operation.
        """
        source = self._interpret_source(source)
        assert source in ["SOUR1", "SOUR2"]
        return self.ask(":MATH:{0}?".format(source))

    def set_math_source(self, channel=1, source=1):
        """
        Set the source of the math operation.
        """
        source = self._interpret_source(source)
        assert source in ["SOUR1", "SOUR2"]
        channel = self._interpret_channel(channel)
        assert channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4"]
        self.write(":MATH:{0} {1}".format(source, channel))

    def get_math_scale(self):
        """
        Query the vertical scale of the operation result. The unit depends on
        the operator currently selected and the unit of the source.
        """
        return self._masked_float(self.ask(":MATH:SCAL?"))

    def set_math_scale(self, scale=1):
        """
        Set the vertical scale of the operation result. The unit depends on the
        operator currently selected and the unit of the source.
        """
        possible_scales = [
            base * 10 ** exp for base in [1, 2, 5] for exp in range(-12, 13)
        ]
        scale = min(possible_scales, key=lambda x: abs(x - scale))
        self.write(":MATH:SCAL {0}".format(scale))

    def get_math_offset(self):
        """
        Query the vertical offset of the operation result. The unit depends on
        the operator currently selected and the unit of the source.
        """
        return self._masked_float(self.ask(":MATH:OFFS?"))

    def set_math_offset(self, offset=0):
        """
        Set the vertical offset of the operation result. The unit depends on
        the operator currently selected and the unit of the source.
        """
        math_scale = self.get_math_scale()
        offset = round(offset * 50 / math_scale, 0) * math_scale / 50.0
        assert abs(offset) <= 1000 * math_scale
        self.write(":MATH:OFFS {0}".format(offset))

    def math_is_inverted(self):
        """
        Query the inverted display mode status of the operation result.
        """
        return bool(int(self.ask(":MATH:INV?")))

    def invert_math(self):
        """
        Enable the inverted display mode of the operation result.
        """
        self.write(":MATH:INV 1")

    def uninvert_math(self):
        """
        Disable the inverted display mode of the operation result.
        """
        self.write(":MATH:INV 0")

    def reset_math(self):
        """
        Sending this command, the instrument adjusts the vertical scale of the
        operation result to the most proper value according to the current
        operator and the horiontal timebase of the source.
        """
        self.write(":MATH:RES")

    def get_fft_window(self):
        """
        Query the window function of the FFT operation.
        """
        return self.ask(":MATH:FFT:WIND?")

    def set_fft_window(self, window="RECT"):
        """
        Set the window function of the FFT operation.
        """
        assert window in ["RECT", "BLAC", "HANN", "HAMM", "FLAT", "TRI"]
        self.write(":MATH:FFT:WIND {0}".format(window))

    def fft_split_is_enabled(self):
        """
        Query the status of the half display mode of the FFT operation.
        """
        return bool(int(self.ask(":MATH:FFT:SPL?")))

    def enable_fft_split(self):
        """
        Enable the half-screen display mode of the FFT operation.
        """
        self.write(":MATH:FFT:SPL 1")

    def disable_fft_split(self):
        """
        Disable the half-screen display mode of the FFT operation.
        """
        self.write(":MATH:FFT:SPL 0")

    def get_fft_unit(self):
        """
        Query the vertical unit of the FFT operation result.
        """
        return self.ask(":MATH:FFT:UNIT?")

    def set_fft_unit(self, unit="DB"):
        """
        Set the vertical unit of the FFT operation result.
        """
        assert unit in ["VRMS", "DB"]
        self.write(":MATH:FFT:UNIT {0}".format(unit))

    def get_fft_horizontal_scale(self):
        """
        Query the horizontal scale of the FFT operation result. The default unit
        is Hz.
        """
        return self._masked_float(self.ask(":MATH:FFT:HSC?"))

    def set_fft_horizontal_scale(self, scale=5e6):
        """
        Set the horizontal scale of the FFT operation result. The default unit
        is Hz.
        """
        possible_scales = [x / self.get_timebase_scale() for x in [5, 2.5, 1, 0.5]]
        scale = min(possible_scales, key=lambda x: abs(x - scale))
        self.write(":MATH:FFT:HSC {0}".format(scale))

    def get_fft_center_frequency(self):
        """
        Query the center frequency of the FFT operation result, namely the
        frequency relative to the horizontal center of the screen. The default
        unit is Hz.
        """
        return self._masked_float(self.ask(":MATH:FFT:HCEN?"))

    def set_fft_center_frequency(self, frequency=5e6):
        """
        Set the center frequency of the FFT operation result, namely the
        frequency relative to the horizontal center of the screen. The default
        unit is Hz.
        """
        if self.get_timebase_scale() <= 1 / frequency / 10:
            self.set_timebase_scale(1 / frequency / 10)
        horizontal_scales = [x / self.get_timebase_scale() for x in [5, 2.5, 1, 0.5]]
        for horizontal_scale in horizontal_scales:
            self.set_fft_horizontal_scale(horizontal_scale)
            frequency = (
                round(frequency * 50 / self.get_fft_horizontal_scale(), 0)
                * self.get_fft_horizontal_scale()
                / 50
            )
            if frequency != 0:
                break
        assert frequency <= 40 / self.get_timebase_scale()
        self.write(":MATH:FFT:HCEN {0}".format(frequency))

    def get_math_start(self):
        """
        Query the start point of the waveform math operation.
        """
        return int(self.ask(":MATH:OPT:STAR?"))

    def set_math_start(self, position=0):
        """
        Set the start point of the waveform math operation.
        """
        position = int(round(position))
        assert position >= 0 and position <= 1199
        self.write(":MATH:OPT:STAR {0}".format(position))

    def get_math_end(self):
        """
        Query the end point of the waveform math operation.
        """
        return int(self.ask(":MATH:OPT:END?"))

    def set_math_end(self, position=1199):
        """
        Set the end point of the waveform math operation.
        """
        position = int(round(position))
        assert position > self.get_math_start() and position <= 1199
        self.write(":MATH:OPT:END {0}".format(position))

    def get_math_sensitivity(self):
        """
        Query the sensitivity of the logic operation. The default unit is div
        (namely the current vertical scale).
        """
        return self._masked_float(self.ask(":MATH:OPT:SENS?"))

    def set_math_sensitivity(self, sensitivity=0):
        """
        Set the sensitivity of the logic operation. The default unit is div
        (namely the current vertical scale).
        """
        assert self.get_math_operator() in ["AND", "OR", "XOR", "NOT"]
        sensitivity = round(sensitivity * 12.5, 0) / 12.5
        assert sensitivity >= 0 and sensitivity <= 0.96
        self.write(":MATH:OPT:SENS {0}".format(sensitivity))

    def get_differential_smoothing_width(self):
        """
        Query the smoothing window width of the differential operation (diff).
        """
        return int(self.ask(":MATH:OPT:DIS?"))

    def set_differential_smoothing_width(self, distance=3):
        """
        Set the smoothing window width of the differential operation (diff).
        """
        assert distance >= 3 and distance <= 201
        self.write(":MATH:OPT:DIS {0}".format(distance))

    def math_autoscale_is_enabled(self):
        """
        Query the status of the auto scale setting.
        """
        return bool(int(self.ask(":MATH:OPT:ASC?")))

    def enable_math_autoscale(self):
        """
        Enable the auto scale setting of the operation result.
        """
        self.write(":MATH:OPT:ASC 1")

    def disable_math_autoscale(self):
        """
        Disable the auto scale setting of the operation result
        """
        self.write(":MATH:OPT:ASC 0")

    def get_math_threshold(self, source=1):
        """
        Query the threshold level of a source in the logic operation. The
        default unit is V.
        """
        assert source in [1, 2]
        return self._masked_float(self.ask(":MATH:OPT:THR{0}?".format(source)))

    def set_math_threshold(self, threshold, source=1):
        """
        Set the threshold level of a source in the logic operation. The default
        unit is V.
        """
        assert source in [1, 2]
        assert self.get_math_operator() in ["AND", "OR", "XOR", "NOT"]
        possible_thresholds = [i * self.get_math_scale() / 25 for i in range(-100, 101)]
        threshold = min(possible_thresholds, key=lambda x: abs(x - threshold))
        self.write(":MATH:OPT:THR{0} {1}".format(source, threshold))

    def mask_is_enabled(self):
        """
        Query the status of the pass/fail test.
        """
        return bool(int(self.ask(":MASK:ENAB?")))

    def enable_mask(self):
        """
        Enable the pass/fail test.
        """
        self.write(":MASK:ENAB 1")

    def disable_mask(self):
        """
        Disable the pass/fail test.
        """
        self.write(":MASK:ENAB 0")

    def get_mask_source(self):
        """
        Query the source of the pass/fail test.
        """
        return self.ask(":MASK:SOUR?")

    def set_mask_source(self, channel=1):
        """
        Set the source of the pass/fail test.
        """
        channel = self._interpret_channel(channel)
        self.write(":MASK:SOUR {0}".format(channel))

    def mask_is_running(self):
        """
        Query the status of the pass/fail test.
        """
        return self.ask(":MASK:OPER?") == "RUN"

    def run_mask(self):
        """
        Run or stop the pass/fail test.
        """
        self.write(":MASK:OPER RUN")

    def stop_mask(self):
        """
        Run or stop the pass/fail test.
        """
        self.write(":MASK:OPER STOP")

    def mask_stats_is_shown(self):
        """
        Query the status of the statistic information.
        """
        return bool(int(self.ask(":MASK:MDIS?")))

    def show_mask_stats(self):
        """
        Enable the statistic information when the pass/fail test is enabled.
        """
        self.write(":MASK:MDIS 1")

    def hide_mask_stats(self):
        """
        Enable the statistic information when the pass/fail test is enabled.
        """
        self.write(":MASK:MDIS 0")

    def mask_stop_on_fail_is_enabled(self):
        """
        Query the status of the "Stop on Fail" function.
        """
        return bool(int(self.ask(":MASK:SOO?")))

    def enable_mask_stop_on_fail(self):
        """
        Turn the "Stop on Fail" function on.
        """
        self.write(":MASK:SOO 1")

    def disable_mask_stop_on_fail(self):
        """
        Turn the "Stop on Fail" function off.
        """
        self.write(":MASK:SOO 0")

    def mask_beeper_is_enabled(self):
        """
        Query the status of the sound prompt.
        """
        return bool(int(self.ask(":MASK:OUTP?")))

    def enable_mask_beeper(self):
        """
        Enable the sound prompt when the failed waveforms are detected.
        """
        self.write(":MASK:OUTP 1")

    def disable_mask_beeper(self):
        """
        Disable the sound prompt when the failed waveforms are detected.
        """
        self.write(":MASK:OUTP 0")

    def get_mask_adjustment(self, axis):
        """
        Query the adjustment parameter in the pass/fail test mask.
        """
        return self._masked_float(self.ask(":MASK:{0}?".format(axis)))

    def set_mask_adjustment(self, axis, adjustment=0.24):
        """
        Set the adjustment parameter in the pass/fail test mask.
        """
        possible_adjustments = [round(0.02 * x, 2) for x in range(201)]
        adjustment = min(possible_adjustments, key=lambda x: abs(x - adjustment))
        self.write(":MASK:{0} {1}".format(axis, adjustment))

    def create_mask(self):
        """
        Create the pass/fail test mark using the current horizontal adjustment
        parameter and vertical adjustment parameter.
        """
        assert self.mask_is_enabled()
        assert not self.mask_is_running()
        self.write(":MASK:CRE")

    def get_passed_mask_frames(self):
        """
        Query the number of passed frames in the pass/fail test.
        """
        return int(self.ask(":MASK:PASS?"))

    def get_failed_mask_frames(self):
        """
        Query the number of failed frames in the pass/fail test.
        """
        return int(self.ask(":MASK:FAIL?"))

    def get_total_mask_frames(self):
        """
        Query the total number of frames in the pass/fail test.
        """
        return int(self.ask(":MASK:TOT?"))

    def reset_mask(self):
        """
        Reset the numbers of the passed frames and the failed frames as well as
        the total number of frames in the pass/fail test to 0.
        """
        return self.write(":MASK:RES")

    def get_measurement_source(self):
        """
        Query the source of the current measurement parameter.
        """
        return self.ask(":MEAS:SOUR?")

    def set_measurement_source(self, channel=1):
        """
        Set the source of the current measurement parameter.
        """
        channel = self._interpret_channel(channel)
        self.write(":MEAS:SOUR {0}".format(channel))

    def get_counter_source(self):
        """
        Query the source of the frequency counter.
        """
        return self.ask(":MEAS:COUN:SOUR?")

    def set_counter_source(self, channel):
        """
        Set the source of the frequency counter.
        """
        channel = self._interpret_channel(channel)
        self.write(":MEAS:COUN:SOUR {0}".format(channel))

    def get_counter_value(self):
        """
        Query the measurement result of the frequency counter. The default unit
        is Hz.
        """
        return self._masked_float(self.ask(":MEAS:COUN:VAL?"))

    def clear_measurement(self, item="ALL"):
        """
        Clear one or all of the last five measurement items enabled.
        """
        item = self._interpret_item(item)
        assert item in ["ITEM1", "ITEM2", "ITEM3", "ITEM4", "ITEM5", "ALL"]
        self.write(":MEAS:CLE {0}".format(item))

    def recover_measurement(self, item="ALL"):
        """
        Recover the measurement item which has been cleared.
        """
        item = self._interpret_item(item)
        assert item in ["ITEM1", "ITEM2", "ITEM3", "ITEM4", "ITEM5", "ALL"]
        self.write(":MEAS:REC {0}".format(item))

    def all_measurements_is_shown(self):
        """
        Query the status of the all measurement function.
        """
        return bool(int(self.ask("MEAS:ADIS?")))

    def show_all_measurements_display(self):
        """
        Enable the all measurement function.
        """
        self.write(":MEAS:ADIS 1")

    def hide_all_measurements_display(self):
        """
        Disable the all measurement function.
        """
        self.write(":MEAS:ADIS 0")

    def get_all_measurements_display_source(self):
        """
        Query the source of the all measurement function.
        """
        return self.ask(":MEAS:AMS?")

    def set_all_measurements_display_source(self, channel=1):
        """
        Set the source of the all measurement function.
        """
        channel = self._interpret_channel(channel)
        self.write(":MEAS:AMS {0}".format(channel))

    def get_measure_threshold_max(self):
        """
        Query the upper limit of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        return int(self.ask(":MEAS:SET:MAX?"))

    def set_measure_threshold_max(self, percent=90):
        """
        Set the upper limit of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        self.write(":MEAS:SET:MAX {0}".format(percent))

    def get_measure_threshold_mid(self):
        """
        Get the middle point of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        return int(self.ask(":MEAS:SET:MAX?"))

    def set_measure_threshold_mid(self, percent=50):
        """
        Set the middle point of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        self.write(":MEAS:SET:MAX {0}".format(percent))

    def get_measure_threshold_min(self):
        """
        Query the lower limit of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        return int(self.ask(":MEAS:SET:MIN?"))

    def set_measure_threshold_min(self, percent=10):
        """
        Set the lower limit of the threshold in the time, delay, and phase
        measurements. The default unit is %.
        """
        self.write(":MEAS:SET:MIN {0}".format(percent))

    def get_measure_phase_source(self, source="A"):
        """
        Query the source of the Phase 1 -> 2 rising and Phase 1 -> 2 falling
        measurements.
        """
        return self.ask("MEAS:SET:PS{0}?".format(source))

    def set_measure_phase_source(self, channel, source="A"):
        """
        Set the source of the Phase 1 -> 2 rising and Phase 1 -> 2 falling
        measurements.
        """
        assert source in ["A", "B"]
        channel = self._interpret_channel(channel)
        self.write(":MEAS:SET:PS{0} {1}".format(source, channel))

    def get_measure_delay_source(self, source="A"):
        """
        Query the source of the Delay 1 -> rising and Delay 1 -> falling
        measurements.
        """
        assert source in ["A", "B"]
        return self.ask(":MEAS:SET:DS{0}?".format(source))

    def set_measure_delay_source(self, channel, source="A"):
        """
        Set the source of the Delay 1 -> rising and Delay 1 -> falling
        measurements.
        """
        assert source in ["A", "B"]
        channel = self._interpret_channel(channel)
        self.write(":MEAS:SET:DS{0} {1}".format(source, channel))

    def statistic_is_shown(self):
        """
        Query the status of the statistic function
        """
        return bool(int(self.ask(":MEAS:STAT:DISP?")))

    def show_statistics(self):
        """
        Enable the statistic function.
        """
        self.write(":MEAS:STAT:DISP 1")

    def hide_statistics(self):
        """
        Disable the statistic function.
        """
        self.write(":MEAS:STAT:DISP 0")

    def get_statistic_mode(self):
        """
        Query the statistic mode.
        """
        return self.ask(":MEAS:STAT:MODE?")

    def set_statistic_mode(self, mode="EXTR"):
        """
        Set the statistic mode.
        """
        assert mode in ["DIFF", "EXTR"]
        self.write(":MEAS:STAT:MODE {0}".format(mode))

    def reset_statistic(self):
        """
        Clear the history data and make statistic again.
        """
        self.write(":MEAS:STAT:RES")

    def get_measurement(self, item, type="CURR", channel=1):
        """
        Query the statistic result of any waveform parameter of the specified
        source.
        """
        channel = self._interpret_channel(channel)
        assert type in ["MAX", "MIN", "CURR", "AVER", "DEV"]
        assert item in [
            "VMAX",
            "VMIN",
            "VTOP",
            "VBAS",
            "VAMP",
            "VAVG",
            "VRMS",
            "OVER",
            "PRES",
            "MAR",
            "MPAR",
            "PER",
            "FREQ",
            "RTIM",
            "FTIM",
            "PWID",
            "NWID",
            "PDUT",
            "NDUT",
            "RDEL",
            "FDEL",
            "RPH",
            "FPH",
        ]
        return self._masked_float(
            self.ask(":MEAS:STAT:ITEM? {0},{1},{2}".format(type, item, channel))
        )

    def show_measurement(self, item, channel=1):
        """
        Set the statistic result of any waveform parameter of the specified
        source.
        """
        channel = self._interpret_channel(channel)
        assert item in [
            "VMAX",
            "VMIN",
            "VTOP",
            "VBAS",
            "VAMP",
            "VAVG",
            "VRMS",
            "OVER",
            "PRES",
            "MAR",
            "MPAR",
            "PER",
            "FREQ",
            "RTIM",
            "FTIM",
            "PWID",
            "NWID",
            "PDUT",
            "NDUT",
            "RDEL",
            "FDEL",
            "RPH",
            "FPH",
        ]
        self.write(":MEAS:STAT:ITEM {0},{1}".format(item, channel))

    def reference_is_shown(self):
        """
        Query the status of the REF function.
        """
        return bool(int(self.ask(":REF:DISP?")))

    def show_reference(self):
        """
        Enable the REF function.
        """
        self.write(":REF:DISP 1")

    def hide_reference(self):
        """
        Disable the REF function.
        """
        self.write(":REF:DISP 0")

    def reference_is_enabled(self, reference=1):
        """
        Query the status of the REF function.
        """
        reference = self._interpret_reference(reference)
        return bool(int(self.ask(":{0}:ENAB?".format(reference))))

    def enable_reference(self, reference=1):
        """
        Enable the ref function.
        """
        reference = self._interpret_reference(reference)
        self.write(":{0}:ENAB 1".format(reference))

    def disable_reference(self, reference=1):
        """
        Enable the ref function.
        """
        reference = self._interpret_reference(reference)
        self.write(":{0}:ENAB 0".format(reference))

    def get_reference_source(self, reference=1):
        """
        Query the source of the specified reference channel.
        """
        reference = self._interpret_reference(reference)
        return self.ask(":{0}:SOUR?".format(reference))

    def set_reference_source(self, channel, reference=1):
        """
        Set the source of the specified reference channel.
        """
        channel = self._interpret_channel(channel)
        reference = self._interpret_reference(reference)
        assert self.channel_is_shown(channel)
        self.write(":{0}:SOUR {1}".format(reference, channel))

    def get_reference_scale(self, reference=1):
        """
        Query the vertical scale of the specified reference channel. The unit is
        the same as the unit of the source.
        """
        reference = self._interpret_reference(reference)
        return self._masked_float(self.ask(":{0}:VSC?".format(reference)))

    def set_reference_scale(self, scale, reference=1):
        """
        Set the vertical scale of the specified reference channel. The unit is
        the same as the unit of the source.
        """
        assert (
            scale >= self.get_probe_ratio() * 1e-3
            and scale <= self.get_probe_ratio() * 10
        )
        reference = self._interpret_reference(reference)
        self.write(":{0}:VSC {1}".format(reference, scale))

    def get_reference_offset(self, reference=1):
        """
        Query the vertical offset of the specified reference channel. The unit
        is the same as the unit of the source.
        """
        reference = self._interpret_reference(reference)
        return self._masked_float(self.ask(":{0}:VOFF?".format(reference)))

    def set_reference_offset(self, offset, reference=1):
        """
        Set the vertical offset of the specified reference channel. The unit is
        the same as the unit of the source.
        """
        reference = self._interpret_reference(reference)
        self.write(":{0}:VOFF {1}".format(reference, offset))

    def reset_reference(self, reference=1):
        """
        Reset the vertical scale and vertical offset of the specified reference
        channel to their default values.
        """
        reference = self._interpret_reference(reference)
        self.write(":{0}:RES".format(reference))

    def source_is_enabled(self, source=1):
        """
        Query the status of the output of the specified source channel.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:OUTP?".format(source)).endswith("N")

    def enable_source(self, source=1):
        """
        Turn on the output of the specified source channel.
        """
        source = self._interpret_source(source)
        self.write(":{0}:OUTP 1".format(source))

    def disable_source(self, source=1):
        """
        Turn off the output of the specified source channel.
        """
        source = self._interpret_source(source)
        self.write(":{0}:OUTP 0".format(source))

    def get_source_impedance(self, source=1):
        """
        Query the impedance of the specified source channel.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:OUTP:IMP?".format(source))

    def set_source_impedance(self, impedance, source=1):
        """
        Set the impedance of the specified source channel.
        """
        source = self._interpret_source(source)
        assert impedance in ["OMEG", "FIFT"]
        self.write(":{0}:OUTP:IMP {1}".format(source, impedance))

    def get_source_frequency(self, source=1):
        """
        Query the output frequency of the specified source channel if the
        modulation is not enabled or the carrier frequency of the modulation is
        enabled. The default unit is Hz.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:FREQ?".format(source)))

    def set_source_frequency(self, frequency, source=1):
        """
        Set the output frequency of the specified source channel if the
        modulation is not enabled or the carrier frequency of the modulation is
        enabled. The default unit is Hz.
        """
        source_function = self.get_source_function()
        if source_function == "SIN":
            assert frequency >= 100e-3 and frequency <= 25e6
        if source_function == "SQU":
            assert frequency >= 100e-3 and frequency <= 15e6
        if source_function == "PULS":
            assert frequency >= 100e-3 and frequency <= 1e6
        if source_function == "RAMP":
            assert frequency >= 100e-3 and frequency <= 100e3
        if source_function == "EXT":
            assert frequency >= 100e-3 and frequency <= 10e6
        source = self._interpret_source(source)
        self.write(":{0}:FREQ {1}".format(source, frequency))

    def get_source_phase(self, source=1):
        """
        Query the start phase of the specified source channel. The default unit
        is degrees.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:PHAS?".format(source)))

    def set_source_phase(self, phase, source=1):
        """
        Set the start phase of the specified source channel. The default unit is
        degrees.
        """
        source = self._interpret_source(source)
        assert phase >= 0 and phase <= 360
        self.write(":{0}:PHAS {1}".format(source, phase))

    def align_source_phases(self, source=1):
        """
        Execute the align phase operation.
        """
        self.write(":{0}:PHAS:INIT")

    def get_source_function(self, source=1):
        """
        Query the output waveform when the modulation of the specified source
        channel is not enabled. Query the carrier waveform when the modulation
        is enabled. At this point, if PULse, NOISe, or DC is selected, the
        modulation will turn off automatically.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:FUNC?".format(source))

    def set_source_function(self, wave, source=1):
        """
        Set the output waveform when the modulation of the specified source
        channel is not enabled. Set the carrier waveform when the modulation is
        enabled. At this point, if PULse, NOISe, or DC is selected, the
        modulation will turn off automatically.
        """
        source = self._interpret_source(source)
        assert wave in ["SIN", "SQU", "RAMP", "PULS", "NOIS", "DC", "INTE", "EXT"]
        self.write(":{0}:FUNC {1}".format(source, wave))

    def get_source_ramp_symmetry(self, source=1):
        """
        Query the ramp symmetry (the percentage that the rising period takes up
        in the whole period) of the specified source channel. The default unit
        is %.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:FUNC:RAMP:SYMM?".format(source)))

    def set_source_ramp_symmetry(self, percent, source=1):
        """
        Set the ramp symmetry (the percentage that the rising period takes up in
        the whole period) of the specified source channel. The default unit is
        %.
        """
        source = self._interpret_source(source)
        self.write(":{0}:FUNC:RAMP:SYMM {1}".format(source, percent))

    def get_source_amplitude(self, source=1):
        """
        Query the output amplitude of the specified source channel. The default
        unit is Vpp.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:VOLT?".format(source)))

    def set_source_amplitude(self, amplitude, source=1):
        """
        Set the output amplitude of the specified source channel. The default
        unit is Vpp.
        """
        source_impedance = self.get_source_impedance()
        if source_impedance == "OMEG":
            assert amplitude >= 20e-3 and amplitude <= 5
        elif source_impedance == "FIFT":
            assert amplitude >= 10e-3 and amplitude <= 2.5
        source = self._interpret_source(source)
        self.write(":{0}:VOLT {1}".format(source, amplitude))

    def get_source_offset(self, source=1):
        """
        Query the DC offset of the specified source channel. The default unit is
        V.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:VOLT:OFFS?".format(source)))

    def set_source_offset(self, offset, source=1):
        """
        Set the DC offset of the specified source channel. The default unit is
        V.
        """
        source_impedance = self.get_source_impedance()
        if source_impedance == "OMEG":
            assert offset <= abs(2.5 - self.get_source_amplitude() / 2)
        elif source_impedance == "FIFT":
            assert offset <= abs(1.25 - self.get_source_amplitude() / 2)
        source = self._interpret_source(source)
        self.write(":{0}:VOLT:OFFS {1}".format(source, offset))

    def get_source_duty_cycle(self, source=1):
        """
        Query the pulse duty cycle (the percentage that the high level takes up
        in the whole period) of the specified source channel. The default unit
        is %.
        """
        source = self._interpret_source(source)
        return self._masked_float(self.ask(":{0}:PULS:DCYC?".format(source)))

    def set_source_duty_cycle(self, percent, source=1):
        """
        Set the pulse duty cycle (the percentage that the high level takes up
        in the whole period) of the specified source channel. The default unit
        is %.
        """
        assert percent >= 10 and percent <= 90
        source = self._interpret_source(source)
        self.write(":{0}:PULS:DCYC {1}".format(source, percent))

    def source_modulation_is_enabled(self, source=1):
        """
        Query the status of the modulation of the specified source channel.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:MOD?".format(source)).endswith("N")

    def enable_source_modulation(self, source=1):
        """
        Enable the modulation of the specified source channel.
        """
        source = self._interpret_source(source)
        self.write(":{0}:MOD 1".format(source))

    def disable_source_modulation(self, source=1):
        """
        Disable the modulation of the specified source channel.
        """
        source = self._interpret_source(source)
        self.write(":{0}:MOD 0".format(source))

    def get_source_modulation_type(self, source=1):
        """
        Query the modulation type of the specified source channel.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:MOD:TYP?".format(source))

    def set_source_modulation_type(self, type, source=1):
        """
        Set the modulation type of the specified source channel.
        """
        source = self._interpret_source(source)
        assert type in ["FM", "AM"]
        self.write(":{0}:MOD:TYP {1}".format(source, type))

    def get_source_modulation_depth(self, source=1):
        """
        Query the AM modulation depth (indicates the amplitude variation degree
        and is expressed as a percentage) of the specified source channel. The
        default unit is %.
        """
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        assert source_modulation_type in ["AM"]
        return int(self.ask(":{0}:MOD:{1}?".format(source, source_modulation_type)))

    def set_source_modulation_depth(self, depth, source=1):
        """

        """
        source_modulation_type = self.get_source_modulation_type(source)
        assert source_modulation_type in ["AM"]
        assert depth >= 0 and depth <= 120
        source = self._interpret_source(source)
        self.write(":{0}:MOD:{1} {2}".format(source, source_modulation_type, depth))

    def get_source_modulation_frequency(self, source=1):
        """
        Query the modulating waveform frequency of the AM or FM of the specified
        source channel. The default unit is Hz.
        """
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        return int(
            self.ask(":{0}:MOD:{1}:INT:FREQ?".format(source, source_modulation_type))
        )

    def set_source_modulation_frequency(self, freq, source=1):
        """
        Set the modulating waveform frequency of the AM or FM of the specified
        source channel. The default unit is Hz.
        """
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        self.write(
            ":{0}:MOD:{1}:INT:FREQ {2}".format(source, source_modulation_type, freq)
        )

    def get_source_modulation_function(self, source=1):
        """
        Query the modulating waveform of AM or FM of the specified source
        channel.
        """
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        return self.ask(":{0}:MOD:{1}:INT:FUNC?".format(source, source_modulation_type))

    def set_source_modulation_function(self, wave, source=1):
        """
        Set the modulating waveform of AM or FM of the specified source channel.
        """
        source = self._interpret_source(source)
        assert wave in ["SIN", "SQU", "RAMP", "NOIS"]
        source_modulation_type = self.get_source_modulation_type(source)
        self.write(
            ":{0}:MOD:{1}:INT:FUNC {2}".format(source, source_modulation_type, wave)
        )

    def get_source_modulation_deviation(self, source=1):
        """
        Query the FM frequency deviation of the specified source channel. The
        default unit is Hz.
        """
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        assert source_modulation_type in ["FM"]
        return int(self.ask(":{0}:MOD:{1}?".format(source, source_modulation_type)))

    def set_source_modulation_deviation(self, deviation, source=1):
        """
        Set the FM frequency deviation of the specified source channel. The
        default unit is Hz.
        """
        assert deviation >= 0 and deviation <= self.get_source_modulation_frequency()
        source = self._interpret_source(source)
        source_modulation_type = self.get_source_modulation_type(source)
        assert source_modulation_type in ["FM"]
        self.write(":{0}:MOD:{1} {2}".format(source, source_modulation_type, deviation))

    def get_source_configuration(self, source=1):
        """
        Query the output configurations of the specified source channel.
        """
        source = self._interpret_source(source)
        return self.ask(":{0}:APPL?".format(source))

    def configure_source(
        self, type="SIN", freq=100e3, amp=1, offset=0, phase=0, source=1
    ):
        """
        Configure the specified source channel to ouput the signal with the
        specified waveform and parameters.
        """
        source = self._interpret_source(source)
        assert type in ["NOIS", "PULS", "RAMP", "SIN", "SQU", "USER"]
        if type == "NOIS":
            self.write(":{0}:APPL:{1} {2},{3}".format(source, type, amp, offset))
        else:
            self.write(
                ":{0}:APPL:{1} {2},{3},{4},{5}".format(
                    source, type, freq, amp, offset, phase
                )
            )

    def manual_autoscale_is_enabled(self):
        """
        Query the status of the auto key.
        """
        return bool(int(self.ask(":SYST:AUT?")))

    def enable_manual_autoscale(self):
        """
        Enable the auto key at the front panel.
        """
        self.write(":SYST:AUT 1")

    def disable_manual_autoscale(self):
        """
        Disable the auto key at the front panel.
        """
        self.write(":SYST:AUT 0")

    def beeper_is_enabled(self):
        """
        Query the status of the beeper.
        """
        return bool(int(self.ask(":SYST:BEEP?")))

    def enable_beeper(self):
        """
        Enable the beeper.
        """
        self.write(":SYST:BEEP 1")

    def disable_beeper(self):
        """
        Disable the beeper.
        """
        self.write(":SYST:BEEP 0")

    def get_error_message(self):
        """
        Query and delete the last system error message.
        """
        return self.ask(":SYST:ERR?")

    def get_gpib(self):
        """
        Query the GPIB address.
        """
        return int(self.ask(":SYST:GPIB?"))

    def set_gpib(self, address):
        """
        Set the GPIB address.
        """
        assert address in range(1, 31)
        self.write(":SYST:GPIB {0}".format(address))

    def get_language(self):
        """
        Query the system language.
        """
        return self.ask(":SYST:LANG?")

    def set_language(self, language="ENGL"):
        """
        Set the system language.
        """
        assert language in ["SCH", "ENGL"]
        self.write(":SYST:LANG {0}".format(language))

    def keyboard_is_locked(self):
        """
        Query the status of the keyboard lock function.
        """
        return bool(int(self.ask(":SYST:LOCK?")))

    def lock_keyboard(self):
        """
        Enable the keyboard lock function.
        """
        self.write(":SYST:LOCK 1")

    def unlock_keyboard(self):
        """
        Disable the keyboard lock function.
        """
        self.write(":SYST:LOCK 0")

    def recall_is_enabled(self):
        """
        Query the system configuration to be recalled when the oscilloscope is
        powered on again after power-off.
        """
        return self.ask(":SYST:PON?") == "LAT"

    def enable_recall(self):
        """
        Set the system configuration to be recalled when the oscilloscope is
        powered on again after power-off.
        """
        self.write(":SYST:PON LAT")

    def disable_recall(self):
        """
        Set the system configuration to be recalled when the oscilloscope is
        powered on again after power-off.
        """
        self.write(":SYST:PON DEF")

    def install_option(self, license):
        """
        Install the option.
        """
        self.write(":SYST:OPT:INST {0}".format(license))

    def uninstall_option(self):
        """
        Uninstall the options installed.
        """
        self.write(":SYST:OPT:UNINST")

    def timebase_delay_is_enabled(self):
        """
        Query the status of the delayed sweep.
        """
        return bool(int(self.ask(":TIM:DEL:ENAB?")))

    def enable_timebase_delay(self):
        """
        Enable the delayed sweep.
        """
        self.write(":TIM:DEL:ENAB 1")

    def disable_timebase_delay(self):
        """
        Enable the delayed sweep.
        """
        self.write(":TIM:DEL:ENAB 0")

    def get_timebase_delay_offset(self):
        """
        Query the delayed timebase offset.
        """
        return self._masked_float(self.ask(":TIM:DEL:OFFS?"))

    def set_timebase_delay_offset(self, offset=0):
        """
        Set the delayed timebase offset.
        """
        timebase_scale = self.get_timebase_scale()
        timebase_offset = self.get_timebase_offset()
        delay_scale = self.get_timebase_delay_scale()
        assert offset >= -6 * (timebase_scale - delay_scale) + timebase_offset
        assert offset <= 6 * (timebase_scale - delay_scale) + timebase_offset
        self.write(":TIM:DEL:OFFS {0}".format(offset))

    def get_timebase_delay_scale(self):
        """
        Query the delayed timebase scale. The default unit is s/div.
        """
        return self._masked_float(self.ask(":TIM:DEL:SCAL?"))

    def set_timebase_delay_scale(self, scale=500e-9):
        """
        Set the delayed timebase scale. The default unit is s/div.
        """
        sample_rate = self.get_sample_rate()
        timebase_scale = self.get_timebase_scale()
        possible_scales = [
            round(j * 10 ** i, 9)
            for i in range(-9, 1)
            for j in [1, 2, 5]
            if j * 10 ** i >= 2 / sample_rate and j * 10 ** i <= timebase_scale
        ]
        min(possible_scales, key=lambda x: abs(x - scale))
        self.write(":TIM:DEL:SCAL {0}".format(scale))

    def get_timebase_offset(self):
        """
        Query the delayed timebase offset. The default unit is s.
        """
        return self._masked_float(self.ask(":TIMebase:MAIN:OFFSet?"))

    def set_timebase_offset(self, offset=0):
        """
        Set the delayed timebase offset. The default unit is s.
        """
        assert not (self.get_timebase_mode() == "ROLL" and self.is_running())
        assert not (
            self.get_timebase_mode() == "YT"
            and self.get_timebase_mode() == 20e-3
            and not self.is_running()
        )
        self.write(":TIMebase:MAIN:OFFSet {0}".format(offset))

    def get_timebase_scale(self):
        """
        Query the delayed timebase scale. The default unit is s/div.
        """
        return self._masked_float(self.ask(":TIMebase:MAIN:SCALe?"))

    def set_timebase_scale(self, scale=1e-6):
        """
        Set the delayed timebase scale. The default unit is s/div.
        """
        timebase_mode = self.get_timebase_mode()
        if timebase_mode == "MAIN":
            possible_scales = [
                base * 10 ** exp
                for base in [1, 2, 5]
                for exp in range(-9, 1)
                if base * 10 ** exp >= 5e-9
            ]
        elif timebase_mode == "ROLL":
            possible_scales = [
                base * 10 ** exp
                for base in [1, 2, 5]
                for exp in range(-9, 1)
                if base * 10 ** exp >= 200e-3
            ]
        scale = min(possible_scales, key=lambda x: abs(x - scale))
        self.write(":TIMebase:MAIN:SCALe {0}".format(scale))

    def get_timebase_mode(self):
        """
        Query the mode of the horizontal timebase.
        """
        return self.ask(":TIM:MODE?")

    def set_timebase_mode(self, mode="MAIN"):
        """
        Set the mode of the horizontal timebase.
        """
        assert mode in ["MAIN", "XY", "ROLL"]
        self.write(":TIM:MODE {0}".format(mode))

    def get_trigger_mode(self):
        """
        Query the trigger type.
        """
        return self.ask(":TRIG:MODE?")

    def set_trigger_mode(self, mode="EDGE"):
        """
        Set the trigger type.
        """
        assert mode in [
            "PULS",
            "RUNT",
            "WIND",
            "NEDG",
            "SLOP",
            "VID",
            "PATT",
            "DEL",
            "TIM",
            "DUR",
            "SHOL",
            "RS232",
            "IIC",
            "SPI",
            "EDGE",
        ]
        self.write(":TRIG:MODE {0}".format(mode))

    def get_trigger_coupling(self):
        """
        Query the trigger coupling type.
        """
        return self.ask(":TRIG:COUP?")

    def set_trigger_coupling(self, coupling="DC"):
        """
        Set the trigger coupling type.
        """
        assert coupling in ["AC", "DC", "LFR", "HFR"]
        self.write(":TRIG:COUP {0}".format(coupling))

    def get_trigger_status(self):
        """
        Query the current trigger status.
        """
        return self.ask(":TRIGger:STATus?")

    def is_running(self):
        return self.get_trigger_status() in ["TD", "WAIT", "RUN", "AUTO"]

    def force_trigger(self):
        """
        Generate a trigger signal forcefully. This command is only applicable to
        the normal and single trigger modes (see the :TRIGger:SWEep command) and
        is equivalent to pressing the FORCE key at the front panel.
        """
        trigger_sweep = self.get_trigger_sweep()
        assert trigger_sweep == "NORM" or trigger_sweep == "SING"
        self.write(":TFORce")

    def get_trigger_sweep(self):
        """
        Query the trigger mode.
        """
        return self.ask(":TRIG:SWE?")

    def set_trigger_sweep(self, mode="AUTO"):
        """
        Set the trigger mode.
        """
        assert mode in ["AUTO", "NORM", "SING"]
        self.write(":TRIG:SWE {0}".format(mode))

    def get_trigger_holdoff(self):
        """
        Query the trigger holdoff time. The default unit is s.
        """
        return self._masked_float(self.ask(":TRIG:HOLD?"))

    def set_trigger_holdoff(self, time=16e-9):
        """
        Set the trigger holdoff time. The default unit is s.
        """
        self.write(":TRIG:HOLD {0}".format(time))

    def trigger_noise_reject_is_enabled(self):
        """
        Query the status of the noise rejection.
        """
        return bool(int(self.ask(":TRIG:NREJ?")))

    def enable_trigger_noise_reject(self):
        """
        Enable the noise rejection.
        """
        self.write(":TRIG:NREJ 1")

    def disable_trigger_noise_reject(self):
        """
        Disable the noise rejection.
        """
        self.write(":TRIG:NREJ 0")

    def get_trigger_source(self):
        """
        Query the trigger source in edge trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["EDGE", "PULS", "SLOP", "VID", "DURAT"]
        return self.ask(":TRIG:{0}:SOUR?".format(trigger_mode))

    def set_trigger_source(self, channel=1):
        """
        Set the trigger source in edge trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["EDGE", "PULS", "SLOP", "VID", "DURAT"]
        channel = self._interpret_channel(channel)
        self.write(":TRIG:{0}:SOUR {1}".format(trigger_mode, channel))

    def get_trigger_direction(self):
        """
        Query the edge type in edge trigger.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["EDGE"]:
            return self.ask(":TRIG:{0}:SLOP?".format(trigger_mode))
        elif trigger_mode in ["VID"]:
            return self.ask(":TRIG:{0}:POL?".format(trigger_mode))
        else:
            raise ValueError

    def set_trigger_direction(self, direction="POS"):
        """
        Set the edge type in edge trigger.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["EDGE"]:
            assert direction in ["POS", "NEG", "RFAL"]
            self.write(":TRIG:{0}:SLOP {1}".format(trigger_mode, direction))
        elif trigger_mode in ["VID"]:
            assert direction in ["POS", "NEG"]
            self.write(":TRIG:{0}:POL {1}".format(trigger_mode, direction))
        else:
            raise ValueError

    def get_trigger_level(self, source=None):
        """
        Query the trigger level. The unit is the same as the current amplitude
        unit.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["EDGE", "PULS", "VID"]:
            return self._masked_float(self.ask(":TRIG:{0}:LEV?".format(trigger_mode)))
        elif trigger_mode in ["PATT"]:
            channel = self._interpret_channel(source)
            assert channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4"]
            return self._masked_float(
                self.ask(":TRIG:{0}:LEV? {1}".format(trigger_mode, channel))
            )
        elif trigger_mode in ["SLOP"]:
            assert source in ["A", "B"]
            return self._masked_float(
                self.ask(":TRIG:{0}:{1}LEV?".format(trigger_mode, source))
            )
        else:
            raise ValueError

    def set_trigger_level(self, level, source=None):
        """
        Set the trigger level in edge trigger. The unit is the same as the
        current amplitude unit.
        """
        trigger_mode = self.get_trigger_mode()
        channel_scale = self.get_channel_scale()
        channel_offset = self.get_channel_offset()
        assert abs(level) <= 5 * channel_scale - channel_offset
        if trigger_mode in ["EDGE", "PULS", "VID"]:
            self.write(":TRIG:{0}:LEV {1}".format(trigger_mode, level))
        elif trigger_mode in ["PATT"]:
            channel = self._interpret_channel(source)
            assert channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4"]
            self.write(":TRIG:{0}:LEV {1},{2}".format(trigger_mode, channel, level))
        elif trigger_mode in ["SLOP"]:
            assert source in ["A", "B"]
            self.write(":TRIG:{0}:{1}LEV {2}".format(trigger_mode, source, level))
        else:
            raise ValueError

    def get_trigger_condition(self):
        """
        Query the trigger condition in pulse width trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["PULS", "SLOP", "DURAT"]
        return self.ask(":TRIG:{0}:WHEN?".format(trigger_mode))

    def set_trigger_condition(self, condition):
        """
        Set the trigger condition in pulse width trigger.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["PULS", "SLOP"]:
            assert condition in ["PGR", "PLES", "NGR", "NLES", "PGL", "NGL"]
            self.write(":TRIG:{0}:WHEN {1}".format(trigger_mode, condition))
        elif trigger_mode in ["DURAT"]:
            assert condition in ["GRE", "LESS", "GLES"]
            self.write(":TRIG:{0}:WHEN {1}".format(trigger_mode, condition))
        else:
            raise ValueError

    def get_trigger_width(self):
        """
        Query the pulse width in pulse width trigger. The default unit is s.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["SLOP"]:
            return self._masked_float(self.ask(":TRIG:{0}:TIME?".format(trigger_mode)))
        elif trigger_mode in ["PULS"]:
            return self._masked_float(self.ask(":TRIG:{0}:WIDT?".format(trigger_mode)))
        else:
            raise ValueError

    def set_trigger_width(self, width):
        """
        Set the pulse width in pulse width trigger. The default unit is s.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["SLOP"]:
            self.write(":TRIG:{0}:TIME {1}".format(trigger_mode, width))
        elif trigger_mode in ["PULS"]:
            self.write(":TRIG:{0}:WIDT {1}".format(trigger_mode, width))
        else:
            raise ValueError

    def get_trigger_upper_width(self):
        """
        Query the upper pulse width in pulse width trigger. The default unit is
        s.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["SLOP", "DURAT"]:
            return self._masked_float(self.ask(":TRIG:{0}:TUPP?".format(trigger_mode)))
        elif trigger_mode in ["PULS"]:
            return self._masked_float(self.ask(":TRIG:{0}:UWID?".format(trigger_mode)))
        else:
            raise ValueError

    def set_trigger_upper_width(self, width=1e-6):
        """
        Set the upper pulse width in pulse width trigger. The default unit is s.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["SLOP", "DURAT"]:
            self.write(":TRIG:{0}:TUPP {1}".format(trigger_mode, width))
        elif trigger_mode in ["PULS"]:
            self.write(":TRIG:{0}:UWID {1}".format(trigger_mode, width))
        else:
            raise ValueError

    def get_trigger_lower_width(self):
        """
        Query the lower pulse width in pulse width trigger. The default unit is
        s.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["SLOP", "DURAT"]:
            return self._masked_float(self.ask(":TRIG:{0}:TLOW?".format(trigger_mode)))
        elif trigger_mode in ["PULS"]:
            return self._masked_float(self.ask(":TRIG:{0}:LWID?".format(trigger_mode)))
        else:
            raise ValueError

    def set_trigger_lower_width(self, width=992e-9):
        """
        Set the lower pulse width in pulse width trigger. The default unit is s.
        """
        trigger_mode = self.get_trigger_mode()
        trigger_condition = self.get_trigger_condition()
        assert trigger_condition in ["PGL", "NGL"]
        if trigger_mode in ["SLOP", "DURAT"]:
            self.write(":TRIG:{0}:TLOW {1}".format(trigger_mode, width))
        elif trigger_mode in ["PULS"]:
            self.write(":TRIG:{0}:LWID {1}".format(trigger_mode, width))
        else:
            raise ValueError

    def get_trigger_window(self):
        """
        Query the vertical window type in slope trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["SLOP"]
        return self.ask(":TRIG:{0}:WIND?".format(trigger_mode))

    def set_trigger_window(self, window="TA"):
        """
        Set the vertical window type in slope trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["SLOP"]
        self.write(":TRIG:{0}:WIND {1}".format(trigger_mode, window))

    def get_trigger_sync_type(self):
        """
        Query the sync type in video trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        return self.ask(":TRIG:{0}:MODE?".format(trigger_mode))

    def set_trigger_sync_type(self, mode="ALIN"):
        """
        Set the sync type in video trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        assert mode in ["ODDF", "EVEN", "LINE", "ALIN"]
        self.write(":TRIG:{0}:MODE {1}".format(trigger_mode, mode))

    def get_trigger_line(self):
        """
        Query the line number when the sync type in video trigger is LINE.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        return int(self.ask(":TRIG:{0}:LINE?".format(trigger_mode)))

    def set_trigger_line(self, line=1):
        """
        Set the line number when the sync type in video trigger is LINE.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        assert line >= 1 and line <= 625
        self.write(":TRIG:{0}:LINE {1}".format(trigger_mode, line))

    def get_trigger_standard(self):
        """
        Query the video standard in video trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        return self.ask(":TRIG:{0}:STAN?".format(trigger_mode))

    def set_trigger_standard(self, standard="NTSC"):
        """
        Set the video standard in video trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert trigger_mode in ["VID"]
        assert standard in ["PALS", "NTSC", "480P", "576P"]
        self.write(":TRIG:{0}:STAN {1}".format(trigger_mode, standard))

    def get_trigger_pattern(self):
        """
        Query the pattern of each channel in pattern trigger.
        """
        trigger_mode = self.get_trigger_mode()
        if trigger_mode in ["PATT"]:
            return self.ask(":TRIG:{0}:PATT?".format(trigger_mode))
        elif trigger_mode in ["DUR"]:
            return self.ask("TRIG:{0}:TYP?")

    def set_trigger_pattern(self, pattern="X,X,X,X"):
        """
        Set the pattern of each channel in pattern trigger.
        """
        trigger_mode = self.get_trigger_mode()
        assert pattern.count(",") == 3
        if trigger_mode in ["PATT"]:
            assert all([x in ["H", "L", "X", "R", "F"] for x in pattern.split(",")])
            self.write(":TRIG:{0}:PATT {1}".format(trigger_mode, pattern))
        elif trigger_mode in ["DUR"]:
            assert all([x in ["H", "L", "X"] for x in pattern.split(",")])
            self.write(":TRIG:{0}:TYP {1}".format(trigger_mode, pattern))

    def get_waveform_source(self):
        """
        Query the channel of which the waveform data will be read.
        """
        return self.ask(":WAV:SOUR?")

    def set_waveform_source(self, channel=1):
        """
        Set the channel of which the waveform data will be read.
        """
        channel = self._interpret_channel(channel)
        self.write(":WAV:SOUR {0}".format(channel))

    def get_waveform_mode(self):
        """
        Query the reading mode used by :WAVeform:DATA?.
        """
        return self.ask(":WAV:MODE?")

    def set_waveform_mode(self, mode="NORM"):
        """
        Set the reading mode used by :WAVeform:DATA?.
        """
        assert mode in ["NORM", "MAX", "RAW"]
        self.write("WAVeform:MODE {0}".format(mode))

    def get_waveform_format(self):
        """
        Query the return format of the waveform data.
        """
        return self.ask(":WAV:FORM?")

    def set_waveform_format(self, format="BYTE"):
        """
        Set the return format of the waveform data.
        """
        assert format in ["WORD", "BYTE", "ASC"]
        self.write(":WAV:FORM {0}".format(format))

    def get_waveform_data(self):
        """
        Read the waveform data.
        """
        return self.ask_raw(":WAV:DATA?".encode("utf-8"))

    def get_waveform_increment(self, axis="X"):
        """
        Query the time difference between two neighboring points of the
        specified channel source.
        """
        assert axis in ["X", "Y"]
        return self._masked_float(self.ask(":WAV:{0}INC?".format(axis)))

    def get_waveform_origin(self, axis="X"):
        """
        Query the time from the trigger point to the reference time of the
        specified channel source.
        """
        assert axis in ["X", "Y"]
        return self._masked_float(self.ask(":WAV:{0}OR?".format(axis)))

    def get_waveform_reference(self, axis="X"):
        """
        Query the reference time of the specified channel source.
        """
        assert axis in ["X", "Y"]
        return self._masked_float(self.ask(":WAV:{0}REF?".format(axis)))

    def get_waveform_start(self):
        """
        Query the start position of internal memory waveform reading.
        """
        return int(self.ask(":WAV:STAR?"))

    def set_waveform_start(self, start=1):
        """
        Set the start position of internal memory waveform reading.
        """
        self.write(":WAV:STAR {0}".format(start))

    def get_waveform_stop(self):
        """
        Query the stop position of internal memory waveform reading.
        """
        return int(self.ask(":WAV:STOP?"))

    def set_waveform_stop(self, stop=1200):
        """
        Set the start position of internal memory waveform reading.
        """
        self.write(":WAV:STOP {0}".format(stop))

    def get_waveform_preamble(self):
        """
        Query and return all the waveform parameters.
        """
        values = self.ask(":WAV:PRE?")
        values = values.split(",")
        assert len(values) == 10
        format, type, points, count, x_reference, y_origin, y_reference = (
            int(val) for val in values[:4] + values[6:7] + values[8:10]
        )
        x_increment, x_origin, y_increment = (
            float(val) for val in values[4:6] + values[7:8]
        )
        return (
            format,
            type,
            points,
            count,
            x_increment,
            x_origin,
            x_reference,
            y_increment,
            y_origin,
            y_reference,
        )

    def get_waveform_samples(self, channel=1):
        """
        Adapted from https://github.com/pklaus/ds1054z
        """
        channel = self._interpret_channel(channel)
        self.set_waveform_source(channel)
        self.set_waveform_format("BYTE")
        (
            format,
            type,
            points,
            count,
            x_increment,
            x_origin,
            x_reference,
            y_increment,
            y_origin,
            y_reference,
        ) = self.get_waveform_preamble()
        self.set_waveform_start(1)
        self.set_waveform_stop(1200)
        tmp_buff = self.get_waveform_data()
        n_header_bytes = int(chr(tmp_buff[1])) + 2
        n_data_bytes = int(tmp_buff[2:n_header_bytes].decode("ascii"))
        buff = tmp_buff[n_header_bytes : n_header_bytes + n_data_bytes]
        assert len(buff) == points
        samples = list(struct.unpack(str(len(buff)) + "B", buff))
        samples = [
            (sample - y_origin - y_reference) * y_increment for sample in samples
        ]
        timebase_scale = self.get_timebase_scale()
        timebase_offset = self.get_timebase_offset()
        x_axis = [
            i * timebase_scale / 10.0 + timebase_offset
            for i in range(-len(samples) // 2, len(samples) // 2)
        ]
        return x_axis, samples

class DP800(vxi11.Instrument):
    def __init__(self, host, *args, **kwargs):
        super(DP800, self).__init__(host, *args, **kwargs)
        idn = self.get_identification()
        match = re.match("RIGOL TECHNOLOGIES,DP8\d\d", idn)
        if not match:
            msg = "Unknown device identification:\n%s\n"
            raise NameError(msg)

    def __str__(self):
        return self.get_identification()

    def _interpret_channel(self, channel):
        """
        Wrapper to allow specifying channels by their name (str) or by their
        number (int)
        """
        if type(channel) == int:
            assert channel <= 3 and channel >= 1
            channel = "CH" + str(channel)
        return channel

    def _interpret_source(self, source):
        """
        Wrapper to allow specifying sources by their name (str) or by their
        number (int)
        """
        if type(source) == int:
            assert source <= 3 and source >= 1
            source = "SOUR" + str(source)
        return source

    def run_analyzer(self):
        """
        When receiving this command, the instrument executes the analysis
        operation according to the current setting.
        """
        self.write(":ANAL:ANAL")

    def get_analyzer_current_time(self):
        """
        Query the current time of the analyzer.
        """
        return int(self.ask(":ANAL:CURRT?"))

    def set_analyzer_current_time(self, time=1):
        """
        Set the current time of the analyzer.
        """
        self.write(":ANAL:CURRT {0}".format(time))

    def get_analyzer_end_time(self):
        """
        Query the end time of the analyzer.
        """
        return int(self.ask(":ANAL:ENDT?"))

    def set_analyzer_end_time(self, time=2):
        """
        Set the end time of the analyzer.
        """
        self.write(":ANAL:ENDT {0}".format(time))

    def get_analyzer_file(self):
        """
        Query the record file currently opened.
        """
        return self.ask(":ANAL:FILE?")

    def set_analyzer_file(self, location):
        """
        Open the specified record file in memory.
        """
        if type(location) is int:
            assert location >= 1 and location <= 10
            self.write(":ANAL:MEM {0}".format(location))
        else:
            assert location.startswith("D:\\")
            self.write(":ANAL:MMEM {0}".format(location))

    def get_analyzer_unit(self):
        """
        Query the analysis object of the analyzer.
        """
        return self.ask(":ANAL:OBJ?")

    def set_analyzer_unit(self, unit="V"):
        """
        Set the analysis object of the analyzer to voltage, current or power.
        """
        assert unit in ["V", "C", "P"]
        self.write(":ANAL:OBJ {0}".format(unit))

    def get_analyzer_result(self):
        """
        Query the analysis results, including the number of groups, median,
        mode, average, variance, range, minimum, maximum and mean deviation
        """
        response = self.ask(":ANAL:RES?")
        data = dict([attr.split(":") for attr in response.split(",")])
        return data

    def set_analyzer_start_time(self, time=1):
        """
        Set the start time of the analyzer.
        """
        self.write(":ANAL:STARTT {0}".format(time))

    def get_analyzer_start_time(self):
        """
        Query the start time of the analyzer.
        """
        return int(self.ask(":ANAL:STARTT?"))

    def get_analyzer_value(self, time=1):
        """
        Query the voltage, current and power at the specified time in the
        record file opened.
        """
        response = self.ask(":ANAL:VAL? {0}".format(time))
        data = dict([attr.split(":") for attr in response.split(",")])
        return data

    def get_channel(self, channel=1):
        """
        Query the voltage/current of the specified channel.
        """
        channel = self._interpret_channel(channel)
        response = self.ask(":APPL? {0}".format(channel))
        data = response.split(",")
        data = {"voltage": Decimal(data[1]), "current": Decimal(data[2])}
        return data

    def set_channel(self, voltage, current, channel=1):
        """
        Select the specified channel as the current channel and set the
        voltage/current of this channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":APPL {0},{1},{2}".format(channel, voltage, current))

    def get_channel_limits(self, channel=1):
        """
        Query the upper limits of the specified channel.
        """
        channel = self._interpret_channel(channel)
        response = self.ask(":APPL? {0}".format(channel))
        data = response.split(",")
        data = {
            "max_voltage": Decimal(
                data[0][data[0].index(":") + 1 : data[0].index("/") - 1]
            ),
            "max_current": Decimal(data[0][data[0].index("/") + 1 : -1]),
        }
        return data

    def get_delay_cycles(self):
        """
        Query the number of cycles of the delayer.
        """
        response = self.ask(":DELAY:CYCLE?")
        if response == "I":
            return response
        else:
            return int(response.split(",")[1])

    def set_delay_cycles(self, cycles=1):
        """
        Set the number of cycles of the delayer
        """
        if cycles == "I":
            self.write(":DELAY:CYCLE {0}".format(cycles))
        else:
            assert cycles >= 1 and cycles <= 99999
            self.write(":DELAY:CYCLE N,{0}".format(cycles))

    def get_delay_end_state(self):
        """
        Query the end state of the delayer.
        """
        return self.ask(":DELAY:ENDS?")

    def set_delay_end_state(self, state="OFF"):
        """
        Set the end state of the delayer.
        """
        self.write(":DELAY:ENDS {0}".format(state))

    def get_delay_groups(self):
        """
        Query the number of output groups of the delayer.
        """
        return int(self.ask(":DELAY:GROUP?"))

    def set_delay_groups(self, groups=1):
        """
        Set the number of output groups of the delayer.
        """
        assert groups >= 1 and groups <= 2048
        self.write(":DELAY:GROUP {0}".format(groups))

    def get_delay_parameters(self, group=0, num_groups=1):
        """
        Query the delayer parameters of the specified groups.
        """
        response = self.ask(":DELAY:PARA? {0},{1}".format(group, num_groups))
        data = [
            dict(zip(["group", "state", "delay"], parameters.split(",")))
            for parameters in response[response.index(",") - 1 : -1].split(";")
        ]
        return data

    def set_delay_parameters(self, group=0, state="OFF", delay=1):
        """
        Set the delayer parameters of the specified group.
        """
        assert delay >= 1 and delay <= 99999
        self.write(":DELAY:PARA {0},{1},{2}".format(group, state, delay))

    def delay_is_enabled(self):
        """
        Query the state of the delay output function of the current channel.
        """
        return self.ask(":DELAY?") == "ON"

    def enable_delay(self):
        """
        Enable the state of the delay output function of the current channel.
        """
        self.write(":DELAY ON")

    def disable_delay(self):
        """
        Disable the state of the delay output function of the current channel.
        """
        self.write(":DELAY OFF")

    def get_delay_generation_pattern(self):
        """
        Query the pattern used when generating state automatically.
        """
        return self.ask(":DELAY:STAT:GEN?")[:-1]

    def set_delay_generation_pattern(self, pattern="01"):
        """
        Select the pattern used when generating state automatically.
        """
        assert pattern in ["01", "10"]
        self.write(":DELAY:STAT:GEN {0}P".format(pattern))

    def get_delay_stop_condition(self):
        """
        Query the stop condition of the delayer.
        """
        response = self.ask(":DELAY:STOP?")
        if response == "NONE":
            return {"condition": "NONE", "value": Decimal("0")}
        else:
            data = dict(list(zip(["condition", "value"], response.split(","))))
            data["value"] = Decimal(data["value"])
            return data

    def set_delay_stop_condition(self, condition="NONE", value=0):
        """
        Set the stop condition of the delayer.
        """
        self.write(":DELAY:STOP {0},{1}".format(condition, value))

    def get_delay_generation_time(self):
        """
        Query the method used to generate time automatically as well as the
        corresponding parameters.
        """
        response = self.ask(":DELAY:TIME:GEN?")
        data = dict(zip(["mode", "timebase", "step"], response.split(",")))
        data["timebase"] = int(data["timebase"])
        data["step"] = int(data["step"])
        return data

    def set_delay_generation_time(self, mode="FIX", timebase=None, step=None):
        """
        Set the method used to generate time automatically and the
        corresponding parameters.
        """
        if timebase is not None:
            assert step is not None
            self.write(":DELAY:TIME:GEN {0},{1},{2}".format(mode, timebase, step))
        else:
            self.write(":DELAY:TIME:GEN {0}".format(mode))

    def get_display_mode(self):
        """
        Query the current display mode.
        """
        return self.ask(":DISP:MODE?")[:4]

    def set_display_mode(self, mode="NORM"):
        """
        Set the current display mode.
        """
        assert mode in ["NORM", "WAVE", "DIAL", "CLAS"]
        self.write(":DISP:MODE {0}".format(mode))

    def enable_screen_display(self):
        """
        Turn on the screen display.
        """
        self.write(":DISP ON")

    def disable_screen_display(self):
        """
        Turn off the screen display.
        """
        self.write(":DISP OFF")

    def screen_display_is_enabled(self):
        """
        Query the current screen display state.
        """
        return self.ask(":DISP?") == "ON"

    def clear_display_text(self):
        """
        Clear the characters displayed on the screen.
        """
        self.write(":DISP:TEXT:CLE")

    def get_display_text(self):
        """
        Query the string currently displayed on the screen.
        """
        return self.ask(":DISP:TEXT?")[1:-1]

    def set_display_text(self, text, x=5, y=110):
        """
        Display the specified string from the specified coordinate on the screen.
        """
        self.write(':DISP:TEXT "{0}",{1},{2}'.format(text, x, y))

    def clear_status(self):
        """
        Clear all the event registers in the register set and clear the error
        queue.
        """
        self.write("*CLS")

    def get_event_status_enable(self):
        """
        Query the enable register for the standard event status register set.
        """
        return int(self.ask("*ESE?"))

    def set_event_status_enable(self, data=0):
        """
        Set the enable register for the standard event status register set.
        """
        assert data >= 0 and data <= 255
        self.write("*ESE {0}".format(data))

    def get_event_status(self):
        """
        Query and clear the event register for the standard event status
        register.
        """
        return int(self.ask("*ESR?"))

    def get_identification(self):
        """
        Query the ID string of the instrument.
        """
        return self.ask("*IDN?")

    def get_vendor(self):
        return self.get_identification().split(",")[0]

    def get_product(self):
        return self.get_identification().split(",")[1]

    def get_serial_number(self):
        return self.get_identification().split(",")[2]

    def get_firmware(self):
        return self.get_identification().split(",")[3]

    def is_busy(self):
        """
        The *OPC? command is used to query whether the current operation is
        finished. The *OPC command is used to set the Operation Complete bit
        (bit 0) in the standard event status register to 1 after the current
        operation is finished.
        """
        return not bool(int(self.ask("*OPC?")))

    def reset(self):
        """
        Restore the instrument to the default state.
        """
        self.write("*RST")

    def get_service_request_enable(self):
        """
        Query the enable register for the status byte register set.
        """
        return int(self.ask("*SRE?"))

    def set_service_request_enable(self, data=0):
        """
        Set the enable register for the status byte register set.
        """
        assert data >= 0 and data <= 255
        self.write("*SRE {0}".format(data))

    def get_status_byte(self):
        """
        Query the event regester for the status byte register. The
        value of the status byte register is set to 0 after this
        command is executed.
        """
        return int(self.ask("*STB?"))

    def self_test_is_passing(self):
        """
        Perform a self-test and then returns the self-test results.
        """
        return not bool(int(self.ask("*TST?")))

    def wait(self):
        """
        Wait for the operation to finish.
        """
        self.write("*WAI")

    def initialize_trigger(self):
        """
        Initialize the trigger system.
        """
        self.write(":INIT")

    def get_coupling_channels(self):
        """
        Query the current trigger coupling channels.
        """
        return self.ask(":INST:COUP?")

    def set_coupling_channels(self, channels):
        """
        Select the trigger coupling channels.
        """
        self.write(":INST:COUP {0}".format(channels))

    def get_selected_channel(self):
        """
        Query the channel currently selected.
        """
        return int(self.ask(":INST:NSEL?"))

    def select_channel(self, channel):
        """
        Select the current channel.
        """
        self.write(":INST:NSEL {0}".format(channel))

    def install_option(self, license):
        """
        Install the options.
        """
        self.write(":LIC:SET {0}".format(license))

    def measure(self, channel):
        """
        Query the voltage, current and power measured on the output terminal of
        the specified channel.
        """
        channel = self._interpret_channel(channel)
        response = self.ask(":MEAS:ALL? {0}".format(channel))
        data = dict(
            zip(
                ["voltage", "current", "power"],
                [Decimal(value) for value in response.split(",")],
            )
        )
        return data

    def measure_current(self, channel):
        """
        Query the current measured on the output terminal of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        return Decimal(self.ask(":MEAS:CURR? {0}".format(channel)))

    def measure_power(self, channel):
        """
        Query the power measured on the output terminal of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        return Decimal(self.ask(":MEAS:POWE? {0}".format(channel)))

    def measure_voltage(self, channel):
        """
        Query the voltage measured on the output terminal of the specified
        channel.
        """
        channel = self._interpret_channel(channel)
        return Decimal(self.ask(":MEAS:VOLT? {0}".format(channel)))

    def get_current_monitor_condition(self):
        """
        Query the current monitor condition of the monitor (the current
        channel).
        """
        return self.ask(":MONI:CURR:COND?")

    def set_current_monitor_condition(self, condition="NONE", logic="NONE"):
        """
        Set the current monitor condition of the monitor (the current channel).
        """
        self.write(":MONI:CURR:COND {0},{1}".format(condition, logic))

    def get_power_monitor_condition(self):
        """
        Query the power monitor condition of the monitor (the current channel).
        """
        return self.ask(":MONI:POWER:COND?")

    def set_power_monitor_condition(self, condition="NONE", logic="NONE"):
        """
        Set the power monitor condition of the monitor (the current channel).
        """
        self.write(":MONI:POWER:COND {0},{1}".format(condition, logic))

    def enable_monitor(self):
        """
        Enable the monitor (the current channel).
        """
        self.write(":MONI ON")

    def disable_monitor(self):
        """
        Disable the monitor (the current channel).
        """
        self.write(":MONI OFF")

    def monitor_is_enabled(self):
        """
        Query the state of the monitor (the current channel)
        """
        return self.ask(":MONI?") == "ON"

    def get_monitor_stop_mode(self):
        """
        Query the stop mode of the monitor (the current channel).
        """
        return self.ask(":MONI:STOP?")

    def enable_monitor_outoff(self):
        """
        Enable the "OutpOff" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP OUTOFF,ON".format())

    def disable_monitor_outoff(self):
        """
        Disable the "OutpOff" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP OUTOFF,OFF".format())

    def enable_monitor_warning(self):
        """
        Enable the "Warning" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP WARN,ON".format())

    def disable_monitor_warning(self):
        """
        Disable the "Warning" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP WARN,OFF".format())

    def enable_monitor_beeper(self):
        """
        Enable the "Beeper" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP BEEPER,ON".format())

    def disable_monitor_beeper(self):
        """
        Disable the "Beeper" mode of the monitor (the current channel).
        """
        self.write(":MONI:STOP BEEPER,OFF".format())

    def get_voltage_monitor_condition(self):
        """
        Query the voltage monitor condition of the monitor (the current
        channel).
        """
        return self.ask(":MONI:VOLT:COND?")

    def set_voltage_monitor_condition(self, condition="NONE", logic="NONE"):
        """
        Set the voltage monitor condition of the monitor (the current channel).
        """
        self.write(":MONI:VOLT:COND {0},{1}".format(condition, logic))

    def get_output_mode(self, channel=None):
        """
        Query the current output mode of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:MODE? {0}".format(channel))
        else:
            return self.ask(":OUTP:MODE?")

    def overcurrent_protection_is_tripped(self, channel=None):
        """
        Query whether OCP occurred on the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:OCP:QUES? {0}".format(channel)) == "YES"
        else:
            return self.ask(":OUTP:OCP:QUES?")

    def clear_overcurrent_protection_trip(self, channel=None):
        """
        Clear the label of the overcurrent protection occurred on the specified
        channel.
        """
        if channel is not None:
            self.write(":OUTP:OCP:CLEAR {0}".format(channel))
        else:
            self.write(":OUTP:OCP:CLEAR")

    def enable_overcurrent_protection(self, channel=None):
        """
        Enable the overcurrent protection (OCP) function of the specified
        channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OCP {0},ON".format(channel))
        else:
            self.write(":OUTP:OCP ON")

    def disable_overcurrent_protection(self, channel=None):
        """
        Disable the overcurrent protection (OCP) function of the specified
        channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OCP {0},OFF".format(channel))
        else:
            self.write(":OUTP:OCP OFF")

    def overcurrent_protection_is_enabled(self, channel=None):
        """
        Query the status of the overcurrent protection (OCP) function of the
        specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:OCP? {0}".format(channel)) == "ON"
        else:
            return self.ask(":OUTP:OCP?") == "ON"

    def get_overcurrent_protection_value(self, channel=None):
        """
        Query the overcurrent protection value of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return Decimal(self.ask(":OUTP:OCP:VAL? {0}".format(channel)))
        else:
            return Decimal(self.ask(":OUTP:OCP:VAL?"))

    def set_overcurrent_protection_value(self, value, channel=None):
        """
        Set the overcurrent protection value of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OCP:VAL {0},{1}".format(channel, value))
        else:
            self.write(":OUTP:OCP:VAL")

    def overvoltage_protection_is_tripped(self, channel=None):
        """
        Query whether OVP occurred on the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:OVP:QUES? {0}".format(channel)) == "YES"
        else:
            return self.ask(":OUTP:OVP:QUES?")

    def clear_overvoltage_protection_trip(self, channel=None):
        """
        Clear the label of the overvoltage protection occurred on the specified
        channel.
        """
        if channel is not None:
            self.write(":OUTP:OVP:CLEAR {0}".format(channel))
        else:
            self.write(":OUTP:OVP:CLEAR")

    def enable_overvoltage_protection(self, channel=None):
        """
        Enable the overvoltage protection (OVP) function of the specified
        channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OVP {0},ON".format(channel))
        else:
            self.write(":OUTP:OVP ON")

    def disable_overvoltage_protection(self, channel=None):
        """
        Disable the overvoltage protection (OVP) function of the specified
        channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OVP {0},OFF".format(channel))
        else:
            self.write(":OUTP:OVP OFF")

    def overvoltage_protection_is_enabled(self, channel=None):
        """
        Query the status of the overvoltage protection (OVP) function of the
        specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:OVP? {0}".format(channel)) == "ON"
        else:
            return self.ask(":OUTP:OVP?") == "ON"

    def get_overvoltage_protection_value(self, channel=None):
        """
        Query the overvoltage protection value of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:OVP:VAL? {0}".format(channel))
        else:
            return self.ask(":OUTP:OVP:VAL?")

    def set_overvoltage_protection_value(self, value, channel=None):
        """
        Set the overvoltage protection value of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:OVP:VAL {0},{1}".format(channel, value))
        else:
            self.write(":OUTP:OVP:VAL")

    def get_output_range(self):
        """
        Query the range currently selected of the channel.
        """
        return self.ask(":OUTP:RANG?")

    def set_output_range(self, range="P20V"):
        """
        Select the current range of the channel.
        """
        assert range in ["P20V", "P40V", "LOW", "HIGH"]
        self.write(":OUTP:RANG {0}".format(range))

    def enable_sense(self, channel=None):
        """
        Enable the Sense function of the channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:SENS {0},ON".format(channel))
        else:
            self.write(":OUTP:SENS ON")

    def disable_sense(self, channel=None):
        """
        Disable the Sense function of the channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:SENS {0},OFF".format(channel))
        else:
            self.write(":OUTP:SENS OFF")

    def sense_is_enabled(self, channel=None):
        """
        Query the status of the Sense function of the channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:SENS? {0}".format(channel)) == "ON"
        else:
            return self.ask(":OUTP:SENS?") == "ON"

    def enable_output(self, channel=None):
        """
        Enable the output of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP {0},ON".format(channel))
        else:
            self.write(":OUTP ON")

    def disable_output(self, channel=None):
        """
        Disable the output of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP {0},OFF".format(channel))
        else:
            self.write(":OUTP OFF")

    def output_is_enabled(self, channel=None):
        """
        Query the status of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP? {0}".format(channel)) == "ON"
        else:
            return self.ask(":OUTP?") == "ON"

    def num_channels(self):
        idn = self.get_identification()
        return int(idn[idn.index("DP8") + 3])

    def enable_tracking(self, channel=None):
        """
        Enable the track function of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:TRAC {0},ON")
        else:
            self.write("OUTP:TRAC ON")

    def disable_tracking(self, channel=None):
        """
        Disable the track function of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            self.write(":OUTP:TRAC {0},OFF")
        else:
            self.write("OUTP:TRAC OFF")

    def tracking_is_enabled(self, channel=None):
        """
        Query the status of the track function of the specified channel.
        """
        if channel is not None:
            channel = self._interpret_channel(channel)
            return self.ask(":OUTP:TRAC? {0}") == "ON"
        else:
            return self.ask("OUTP:TRAC?") == "ON"

    def get_record_destination(self):
        """
        Query the storage directory of the record file.
        """
        return self.ask(":REC:DEST?")

    def set_record_destination(self, file_name="RIGOL.ROF", location=10):
        """
        Store the record file to the specified storage location in the internal
        memory with the specified filename.
        """
        assert file_name.endswith(".ROF")
        assert location >= 1 and location <= 10
        self.write(":REC:MEM {0},{1}".format(location, file_name))

    def set_record_destination_external(self, file_path):
        """
        Store the record file to the specified storage directory in the
        external memory.
        """
        assert file_path.startswith("D:\\") and file_path.endswith(".ROF")
        self.write(":REC:MMEM {0}".format(file_path))

    def get_record_period(self):
        """
        Query the current record period of the recorder.
        """
        return int(self.ask(":REC:PERI?"))

    def set_record_period(self, period=1):
        """
        Query the current record period of the recorder.
        """
        self.write(":REC:PERI {0}".format(period))

    def enable_record(self):
        """
        Enable the recorder.
        """
        self.write(":REC ON")

    def disable_record(self):
        """
        Disable the recorder.
        """
        self.write(":REC OFF")

    def record_is_enabled(self):
        """
        Query the status of the recorder.
        """
        return self.ask(":REC?") == "ON"

    def get_channel_current(self, source=None):
        """
        Query the current of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            return Decimal(self.ask(":{0}:CURR?".format(source)))
        else:
            return Decimal(self.ask(":CURR?"))

    def set_channel_current(self, value, source=None):
        """
        Set the current of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            self.write(":{0}:CURR {1}".format(source, value))
        else:
            self.write(":CURR {0}".format(value))

    def get_channel_current_increment(self, source=None):
        """
        Query the step of the current change of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            return Decimal(self.ask(":{0}:CURR:STEP?".format(source))[:-1])
        else:
            return Decimal(self.ask(":CURR:STEP?")[:-1])

    def set_channel_current_increment(self, value, source=None):
        """
        Set the step of the current change of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            self.write(":{0}:CURR:STEP {1}".format(source, value))
        else:
            self.write(":CURR:STEP {0}".format(value))

    def get_channel_current_trigger(self, source=None):
        """
        Query the trigger current of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            return Decimal(self.ask(":{0}:CURR:TRIG?".format(source))[:-1])
        else:
            return Decimal(self.ask(":CURR:TRIG?")[:-1])

    def set_channel_current_trigger(self, value, source=None):
        """
        Set the trigger current of the specified channel.
        """
        if source is not None:
            source = self._interpret_source(source)
            self.write(":{0}:CURR:TRIG {1}".format(source, value))
        else:
            self.write(":CURR:TRIG {0}".format(value))

    def beep(self):
        """
        Send this command and the beeper immediately sounds.
        """
        self.write(":SYST:BEEP:IMM")

    def enable_beeper(self):
        """
        Enable the beeper.
        """
        self.write(":SYST:BEEP ON")

    def disable_beeper(self):
        """
        Disable the beeper.
        """
        self.write(":SYST:BEEP OFF")

    def beeper_is_enabled(self):
        """
        Query the status of the beeper.
        """
        return self.ask(":SYST:BEEP?") == "ON"

    ######################################################
    def get_brightness(self):
        """
        Query the brightness of the screen.
        """
        return int(self.ask(":SYST:BRIG?"))

    def set_brightness(self, brightness=50):
        """
        Set the brightness of the screen.
        """
        self.write(":SYST:BRIG {0}".format(brightness))

    def get_gpib_address(self):
        """
        Query the current GPIB address.
        """
        return int(self.ask(":SYST:COMM:GPIB:ADDR?"))

    def set_gpib_address(self, address=2):
        """
        Set the current GPIB address.
        """
        self.write(":SYST:COMM:GPIB:ADDR {0}".format(address))

    def apply_lan_settings(self):
        """
        Apply the network parameters currently set.
        """
        self.write(":SYST:COMM:LAN:APPL")

    def enable_auto_ip(self):
        """
        Enable the auto IP configuration mode.
        """
        self.write(":SYST:COMM:LAN:AUTO ON")

    def disable_auto_ip(self):
        """
        Disable the auto IP configuration mode.
        """
        self.write(":SYST:COMM:LAN:AUTO OFF")

    def auto_ip_is_enabled(self):
        """
        Query the status of the auto IP configuration mode.
        """
        return self.ask(":SYST:COMM:LAN:AUTO?") == "ON"

    def enable_dhcp(self):
        """
        Enable the DHCP configuration mode.
        """
        self.write(":SYST:COMM:LAN:DHCP ON")

    def disable_dhcp(self):
        """
        Disable the DHCP configuration mode.
        """
        self.write(":SYST:COMM:LAN:DHCP OFF")

    def dhcp_is_enabled(self):
        """
        Query the status of the DHCP configuration mode.
        """
        return self.ask(":SYST:COMM:LAN:DHCP?") == "ON"

    def get_dns(self):
        """
        Query the current DNS address.
        """
        return self.ask(":SYST:COMM:LAN:DNS?")

    def set_dns(self, address):
        """
        Set the current DNS address.
        """
        self.write(":SYST:COMM:LAN:DNS {0}".format(address))

    def get_gateway(self):
        """
        Query the current default gateway.
        """
        return self.ask(":SYST:COMM:LAN:GATE?")

    def set_gateway(self, gateway):
        """
        Set the current default gateway.
        """
        self.write(":SYST:COMM:LAN:GATE {0}".format(gateway))

    def get_ip_address(self):
        """
        Query the current IP address.
        """
        return self.ask(":SYST:COMM:LAN:IPAD?")

    def set_ip_address(self, address):
        """
        Set the IP address.
        """
        self.write(":SYST:COMM:LAN:IPAD {0}".format(address))

    def get_mac_address(self):
        """
        Query the MAC address.
        """
        return self.ask(":SYST:COMM:LAN:MAC?")

    def enable_manual_ip(self):
        """
        Enable the manual IP configuration mode.
        """
        self.write(":SYST:COMM:LAN:MAN ON")

    def disable_manual_ip(self):
        """
        Disable the manual IP configuration mode.
        """
        self.write(":SYST:COMM:LAN:MAN OFF")

    def manual_ip_is_enabled(self):
        """
        Query the status of the manual IP configuration mode.
        """
        return self.ask(":SYST:COMM:LAN:MAN?") == "ON"

    def get_subnet_mask(self):
        """
        Query the current subnet mask.
        """
        return self.ask(":SYST:COMM:LAN:SMASK?")

    def set_subnet_mask(self, mask):
        """
        Set the subnet mask.
        """
        self.write(":SYST:COMM:LAN:SMASK {0}".format(mask))

    def get_baud(self):
        """
        Query the baud rate of the RS232 interface.
        """
        return int(self.ask(":SYST:COMM:RS232:BAUD?"))

    def set_baud(self, rate):
        """
        Set the baud rate of the RS232 interface and the unit is Baud.
        """
        assert rate in [4800, 7200, 9600, 14400, 19200, 38400, 57600, 115200, 128000]
        self.write(":SYST:COMM:RS232:BAUD {0}".format(rate))

    def get_data_bit(self):
        """
        Query the data bit of the RS232 interface.
        """
        return int(self.ask(":SYST:COMM:RS232:DATAB?"))

    def set_data_bit(self, data=8):
        """
        Set the data bit of the RS232 interface.
        """
        assert data in [5, 6, 7, 8]
        self.write(":SYST:COMM:RS232:DATAB {0}".format(data))

    def enable_hardware_flow_control(self):
        """
        Enable the hardware flow control.
        """
        self.write(":SYST:COMM:RS232:FLOWC ON")

    def disable_hardware_flow_control(self):
        """
        Disable the hardware flow control.
        """
        self.write(":SYST:COMM:RS232:FLOWC OFF")

    def hardware_flow_control_is_enabled(self):
        """
        Query the status of the hardware flow control.
        """
        return self.ask(":SYST:COMM:RS232:FLOWC?") == "ON"

    def get_parity_mode(self):
        """
        Query the current parity mode.
        """
        return self.ask(":SYST:COMM:RS232:PARI?")

    def set_parity_mode(self, mode="NONE"):
        """
        Set the parity mode.
        """
        assert mode in ["NONE", "ODD", "EVEN"]
        self.write(":SYST:COMM:RS232:PARI {0}".format(mode))

    def get_stop_bit(self):
        """
        Query the current stop bit.
        """
        return int(self.ask(":SYST:COMM:RS232:STOPB?"))

    def set_stop_bit(self, data=1):
        """
        Set the stop bit.
        """
        assert data in [1, 2]
        self.write(":SYST:COMM:RS232:STOPB {0}".format(data))

    def get_contrast(self):
        """
        Query the contrast of the screen.
        """
        return int(self.ask(":SYST:CONT?"))

    def set_contrast(self, contrast=25):
        """
        Set the contrast of the screen.
        """
        assert contrast >= 1 and contrast <= 100
        self.write(":SYST:CONT {0}".format(contrast))

    def get_error(self):
        """
        Query and clear the error messages in the error queue.
        """
        return self.ask(":SYST:ERR?")

    def enable_remote_lock(self):
        """
        Enable the remote lock.
        """
        self.write(":SYST:KLOC:STAT ON")

    def disable_remote_lock(self):
        """
        Disable the remote lock.
        """
        self.write(":SYST:KLOC:STAT OFF")

    def remote_lock_is_enabled(self):
        """
        Query the status of the remote lock.
        """
        return self.ask(":SYST:KLOC:STAT?") == "ON"

    def get_language(self):
        """
        Query the current system language type.
        """
        return self.ask(":SYST:LANG:TYPE?")

    def set_language(self, language="EN"):
        """
        Set the system language.
        """
        assert language in ["EN", "CH", "JAP", "KOR", "GER", "POR", "POL", "CHT", "RUS"]
        self.write(":SYST:LANG:TYPE {0}".format(language))

    def lock_keyboard(self):
        """
        Lock the front panel.
        """
        self.write(":SYST:LOCK ON")

    def unlock_keyboard(self):
        """
        Unlock the front panel.
        """
        self.write(":SYST:LOCK OFF")

    def keyboard_is_locked(self):
        """
        Query whether the front panel is locked.
        """
        return self.ask(":SYST:LOCK?") == "ON"

    def enable_sync(self):
        """
        Turn on the on/off sync function.
        """
        self.write(":SYST:ONOFFS ON")

    def disable_sync(self):
        """
        Turn off the on/off sync function.
        """
        self.write(":SYST:ONOFFS OFF")

    def sync_is_enabled(self):
        """
        Query whether the on/off sync function is turned on.
        """
        return self.ask(":SYST:ONOFFS?") == "ON"

    def enable_overtemperature_protection(self):
        """
        Enable the over-temperature protection (OTP) function.
        """
        self.write(":SYST:OTP ON")

    def disable_overtemperature_protection(self):
        """
        Disable the over-temperature protection (OTP) function.
        """
        self.write(":SYST:OTP OFF")

    def overtemperature_protection_is_enabled(self):
        """
        Query the status of the over-temperature protection function.
        """
        return self.ask(":SYST:OTP?") == "ON"

    def enable_recall(self):
        """
        The instrument uses the system configuration (including all the system
        parameters and states except the channel output on/off states) before
        the last power-off at power-on.
        """
        self.write(":SYST:POWE LAST")

    def disable_recall(self):
        """
        The instrument uses the factory default values at power-on (except
        those parameters that will not be affected by reset.
        """
        self.write(":SYST:POWE DEF")

    def recall_is_enabled(self):
        """
        Query the status of the power-on mode.
        """
        return self.ask(":SYST:POWE?") == "LAST"

    def get_luminosity(self):
        """
        Query the RGB brightness of the screen.
        """
        return int(self.ask(":SYST:RGBB?"))

    def set_luminosity(self, luminosity=50):
        """
        Set the RGB brightness of the screen.
        """
        assert luminosity >= 1 and luminosity <= 100
        self.write(":SYST:RGBB {0}".format(luminosity))

    def enable_screen_saver(self):
        """
        Enable the screen saver function.
        """
        self.write(":SYST:SAV ON")

    def disable_screen_saver(self):
        """
        Disable the screen saver function.
        """
        self.write(":SYST:SAV OFF")

    def screen_saver_is_enabled(self):
        """
        Query the status of the screen saver function.
        """
        return self.ask(":SYST:SAV?") == "ON"

    def top_board_is_passing(self):
        """
        Query the self-test results of TopBoard.
        """
        return self.ask(":SYST:SELF:TEST:BOARD?").split(",")[0] == "PASS"

    def bottom_board_is_passing(self):
        """
        Query the self-test results of BottomBoard.
        """
        return self.ask(":SYST:SELF:TEST:BOARD?").split(",")[1] == "PASS"

    def fan_is_passing(self):
        """
        Query the self-test results of the fan.
        """
        return self.ask(":SYST:SELF:TEST:FAN?") == "PASS"

    def get_temperature(self):
        """
        Query the self-test result of the temperature.
        """
        return Decimal(self.ask(":SYST:SELF:TEST:TEMP?"))

    def get_track_mode(self):
        """
        Query the current track mode.
        """
        return self.ask(":SYST:TRACKM?")

    def set_track_mode(self, mode="SYNC"):
        """
        Set the track mode.
        """
        assert mode in ["SYNC", "INDE"]
        self.write(":SYST:TRACKM {0}".format(mode))

    def get_system_version(self):
        """
        Query the SCPI version number of the system
        """
        return self.ask(":SYST:VERS?")

    def get_timer_cycles(self):
        """
        Query the current number of cycles of the timer.
        """
        response = self.ask(":TIME:CYCLE?")
        if response.startswith("N,"):
            return int(response[2:])
        else:
            return response

    def set_timer_cycles(self, cycles="I"):
        """
        Set the number of cycles of the timer.
        """
        if cycles == "I":
            self.write(":TIME:CYCLE {0}".format(cycles))
        else:
            assert cycles >= 1 and cycles <= 99999
            self.write(":TIME:CYCLE N,{0}".format(cycles))

    def get_timer_end_state(self):
        """
        Query the current end state of the timer.
        """
        return self.ask(":TIME:ENDS?")

    def set_timer_end_state(self, state="OFF"):
        """
        Set the end state of the timer.
        """
        assert state in ["OFF", "LAST"]
        self.write(":TIME:ENDS {0}".format(state))

    def get_timer_groups(self):
        """
        Query the current number of output groups of the timer.
        """
        return int(self.ask(":TIME:GROUP?"))

    def set_timer_groups(self, num_groups=1):
        """
        Set the number of output groups of the timer.
        """
        assert num_groups >= 1 and num_groups <= 2048
        self.write(":TIME:GROUP {0}".format(num_groups))

    def get_timer_parameters(self, group=None, num_groups=1):
        """
        Query the timer parameters of the specified groups.
        """
        assert group >= 0 and group <= 2047
        assert num_groups >= 1 and num_groups <= 2048
        return self.ask(":TIME:PARA? {0},{1}".format(group, num_groups))

    def set_timer_parameters(self, group, voltage, current=1, delay=1):
        """
        Set the timer parameters of the specified group.
        """
        assert group >= 0 and group <= 2047
        assert delay >= 1 and delay <= 99999
        self.write(":TIME:PARA {0},{1},{2},{3}".format(group, voltage, current, delay))

    def enable_timer(self):
        """
        Enable the timing output function.
        """
        self.write(":TIME ON")

    def disable_timer(self):
        """
        Disable the timing output function.
        """
        self.write(":TIME OFF")

    def timer_is_enabled(self):
        """
        Query the status of the timing output function.
        """
        return self.ask(":TIME?") == "ON"

    def reconstruct_timer(self):
        """
        Send this command and the instrument will create the timer parameters
        according to the templet currently selected and the parameters set.
        """
        self.write(":TIME:TEMP:CONST")

    def get_timer_exp_fall_rate(self):
        """
        Query the fall index of ExpFall.
        """
        return int(self.ask(":TIME:TEMP:FALLR?"))

    def set_timer_exp_fall_rate(self, rate=0):
        """
        Set the fall index of ExpFall.
        """

        assert rate >= 0 and rate <= 10
        self.write(":TIME:TEMP:FALLR {0}".format(rate))

    def get_timer_interval(self):
        """
        Query the current time interval.
        """
        return int(self.ask(":TIME:TEMP:INTE?"))

    def set_timer_interval(self, interval=1):
        """
        Set the time interval.
        """
        assert interval >= 1 and interval <= 99999
        self.write(":TIME:TEMP:INTE {0}".format(interval))

    def enable_timer_invert(self):
        """
        Enable the invert function of the templet currently selected.
        """
        self.write(":TIME:TEMP:INVE ON")

    def disable_timer_invert(self):
        """
        Disable the invert function of the templet currently selected.
        """
        self.write(":TIME:TEMP:INVE OFF")

    def timer_is_inverted(self):
        """
        Query whether the invert function of the templet currently selected is
        enabled.
        """
        return self.ask(":TIME:TEMP:INVE?") == "ON"

    def get_timer_max_value(self):
        """
        Query the maximum voltage or current of the templet currently selected.
        """
        return Decimal(self.ask(":TIME:TEMP:MAXV?"))

    def set_timer_max_value(self, value):
        """
        Set the maximum voltage or current of the templet currently selected.
        """
        self.write(":TIME:TEMP:MAXV {0}".format(value))

    def get_timer_min_value(self):
        """
        Query the minimum voltage or current of the templet currently selected.
        """
        return Decimal(self.ask(":TIME:TEMP:MINV?"))

    def set_timer_min_value(self, value=0):
        """
        Set the minimum voltage or current of the templet currently selected.
        """
        self.write(":TIME:TEMP:MINV {0}".format(value))

    def get_timer_unit(self):
        """
        Query the editing object of the templet currently selected as well as
        the corresponding current or voltage.
        """
        return self.ask(":TIME:TEMP:OBJ?")

    def set_timer_unit(self, unit="V", value=0):
        """
        Select the editing object of the templet and set the current or
        voltage.
        """
        assert unit in ["V", "C"]
        self.write(":TIME:TEMP:OBJ {0},{1}".format(unit, value))

    def get_timer_pulse_period(self):
        """
        Query the period of Pulse.
        """
        return int(self.ask(":TIME:TEMP:PERI?"))

    def set_timer_pulse_period(self, value=10):
        """
        Set the period of Pulse.
        """
        assert value >= 2 and value <= 99999
        self.write(":TIME:TEMP:PERI {0}".format(value))

    def get_timer_points(self):
        """
        Query the total number of points
        """
        return int(self.ask(":TIME:TEMP:POINT?"))

    def set_timer_points(self, value=10):
        """
        Set the total number of points.
        """
        assert value >= 10 and value <= 2048
        self.write(":TIME:TEMP:POINT {0}".format(value))

    def get_timer_exp_rise_rate(self):
        """
        Query the rise index of ExpRise.
        """
        return int(self.ask(":TIME:TEMP:RISER?"))

    def set_timer_exp_rise_rate(self, rate=0):
        """
        Set the rise index of ExpRise.
        """
        assert rate >= 0 and rate <= 10
        self.write(":TIME:TEMP:RISER {0}".format(rate))

    def get_timer_template(self):
        """
        Query the templet type currently selected
        """
        return self.ask(":TIME:TEMP:SEL?")

    def set_timer_template(self, mode="SINE"):
        """
        Select the desired templet type.
        """
        assert mode in ["SINE", "SQUARE", "RAMP", "UP", "DN", "UPDN", "RISE", "FALL"]
        self.write(":TIME:TEMP:SEL {0}".format(mode))

    def get_timer_ramp_symmetry(self):
        """
        Query the symmetry of RAMP.
        """
        return int(self.ask(":TIME:TEMP:SYMM?"))

    def set_timer_ramp_symmetry(self, symmetry=50):
        """
        Set the symmetry of RAMP.
        """
        assert symmetry >= 0 and symmetry <= 100
        self.write(":TIME:TEMP:SYMM {0}".format(symmetry))

    def get_timer_pulse_width(self):
        """
        Query the positive pulse width of Pulse.
        """
        return int(self.ask(":TIME:TEMP:WIDT?"))

    def set_timer_pulse_width(self, width=5):
        """
        Set the positive pulse width of Pulse.
        """
        assert width >= 1 and width <= 99998
        self.write(":TIME:TEMP:WIDT {0}".format(width))

    def get_trigger_source_type(self):
        """
        Query the trigger source type currently selected.
        """
        return self.ask(":TRIG:IN:CHTY?")

    def set_trigger_source_type(self, mode="BUS"):
        """
        Select the trigger source type
        """
        assert mode in ["BUS", "IMM"]
        self.write(":TRIG:IN:CHTY {0}".format(mode))

    def set_trigger_current(self, current=0.1, channel=1):
        """
        Set the trigger current of the specified channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":TRIG:IN:CURR {0},{1}".format(channel, current))

    def enable_trigger_input(self, data_line=None):
        """
        Enable the trigger input function of the specified data line.
        """
        if data_line is not None:
            self.write(":TRIG:IN {0},ON".format(data_line))
        else:
            self.write(":TRIG:IN ON")

    def disable_trigger_input(self, data_line=None):
        """
        Disable the trigger input function of the specified data line.
        """
        if data_line is not None:
            self.write(":TRIG:IN {0},OFF".format(data_line))
        else:
            self.write(":TRIG:IN OFF")

    def trigger_input_is_enabled(self, data_line="D0"):
        """
        Query the status of the trigger input function of the specified data line.
        """
        return self.ask(":TRIG:IN? {0}".format(data_line)) == "{0},ON".format(data_line)

    def trigger(self):
        """
        Initialize the trigger system.
        """
        self.write(":TRIG:IN:IMME")

    def get_trigger_response(self, data_line=None):
        """
        Query the output response of the trigger input of the specified data line
        """
        if data_line is not None:
            return self.ask(":TRIG:IN:RESP? {0}".format(data_line))
        else:
            return self.ask(":TRIG:IN:RESP?")

    def set_trigger_response(self, mode="OFF", data_line=None):
        """
        Set the output response of the trigger input of the specified data line.
        """
        assert mode in ["ON", "OFF", "ALTER"]
        if data_line is not None:
            self.write(":TRIG:IN:RESP {0},{1}".format(data_line, mode))
        else:
            self.write(":TRIG:IN:RESP {0}".format(mode))

    def get_trigger_sensitivity(self, data_line=None):
        """
        Query the trigger sensitivity of the trigger input of the specified data line.
        """
        if data_line is not None:
            return self.ask(":TRIG:IN:SENS? {0}".format(data_line))
        else:
            return self.ask(":TRIG:IN:SENS?")

    def set_trigger_sensitivity(self, sensitivity="LOW", data_line=None):
        """
        Set the trigger sensitivity of the trigger input of the specified data line.
        """
        assert sensitivity in ["LOW", "MID", "HIGH"]
        if data_line is not None:
            self.write(":TRIG:IN:SENS {0},{1}".format(data_line, sensitivity))
        else:
            self.write(":TRIG:IN:SENS {0}".format(sensitivity))

    def get_trigger_input_source(self, data_line=None):
        """
        Query the source under control of the trigger input of the specified data line.
        """
        if data_line is not None:
            return self.ask(":TRIG:IN:SOUR? {0}".format(data_line))
        else:
            return self.ask(":TRIG:IN:SOUR?")

    def set_trigger_input_source(self, channel=1, data_line=None):
        """
        Set the source under control of the trigger input of the specified data line.
        """
        channel = self._interpret_channel(channel)
        if data_line is not None:
            self.write(":TRIG:IN:SOUR {0},{1}".format(data_line, channel))
        else:
            self.write(":TRIG:IN:SOUR {0}".format(channel))

    def get_trigger_type(self, data_line=None):
        """
        Query the trigger type of the trigger input of the specified data line.
        """
        if data_line is not None:
            return self.ask(":TRIG:IN:TYPE? {0}".format(data_line))
        else:
            return self.ask(":TRIG:IN:TYPE?")

    def set_trigger_type(self, mode="RISE", data_line=None):
        """
        Set the trigger type of the trigger input of the specified data line.
        """
        assert mode in ["RISE", "FALL", "HIGH", "LOW"]
        if data_line is not None:
            self.write(":TRIG:IN:TYPE {0},{1}".format(data_line, mode))
        else:
            self.write(":TRIG:IN:TYPE {0}".format(mode))

    def set_trigger_voltage(self, voltage=0, channel=1):
        """
        Set the trigger voltage of the specified channel.
        """
        channel = self._interpret_channel(channel)
        self.write(":TRIG:IN:VOLT {0},{1}".format(channel, voltage))

    def get_trigger_condition(self, data_line=None):
        """
        Query the trigger condition of the trigger output of the specified data line.
        """
        if data_line is not None:
            return self.ask(":TRIG:OUT:COND? {0}".format(data_line))
        else:
            return self.ask(":TRIG:OUT:COND?")

    def set_trigger_condition(self, condition="OUTOFF", value=0, data_line=None):
        """
        Set the trigger condition of the trigger output of the specified data line.
        """
        assert condition in [
            "OUTOFF",
            "OUTON",
            ">V",
            "<V",
            "=V",
            ">C",
            "<C",
            "=C",
            ">P",
            "<P",
            "=P",
            "AUTO",
        ]
        if data_line is not None:
            self.write(":TRIG:OUT:COND {0},{1},{2}".format(data_line, condition, value))
        else:
            self.write(":TRIG:OUT:COND {0},{1}".format(condition, value))

    def get_trigger_duty_cycle(self, data_line=None):
        """
        Query the duty cycle of the square waveform of the trigger output on the
        specified data line.
        """
        if data_line is not None:
            return int(self.ask(":TRIG:OUT:DUTY? {0}".format(data_line)))
        else:
            return int(self.ask(":TRIG:OUT:DUTY?"))

    def set_trigger_duty_cycle(self, duty_cycle=50, data_line=None):
        """
        Set the duty cycle of the square waveform of the trigger output on the
        specified data line.
        """
        assert duty_cycle >= 10 and duty_cycle <= 90
        if data_line is not None:
            self.write(":TRIG:OUT:DUTY {0},{1}".format(data_line, duty_cycle))
        else:
            self.write(":TRIG:OUT:DUTY {0}".format(duty_cycle))

    def enable_trigger_output(self, data_line=None):
        """
        Enable the trigger output function of the specified data line.
        """
        if data_line is not None:
            self.write(":TRIG:OUT {0},ON".format(data_line))
        else:
            self.write(":TRIG:OUT ON")

    def disable_trigger_output(self, data_line=None):
        """
        Disable the trigger output function of the specified data line.
        """
        if data_line is not None:
            self.write(":TRIG:OUT {0},OFF".format(data_line))
        else:
            self.write(":TRIG:OUT OFF")

    def trigger_output_is_enabled(self, data_line="D0"):
        """
        Query the status of the trigger output function of the specified data line.
        """
        return self.ask(":TRIG:OUT? {0}".format(data_line)) == "{0},ON".format(
            data_line
        )

    def get_trigger_period(self, data_line=None):
        """
        Query the period of the square waveform of the trigger output on the
        specified data line.
        """
        if data_line is not None:
            return Decimal(self.ask(":TRIG:OUT:PERI? {0}".format(data_line)))
        else:
            return Decimal(self.ask(":TRIG:OUT:PERI?"))

    def set_trigger_period(self, period=1, data_line=None):
        """
        Set the period of the square waveform of the trigger output on the
        specified data line.
        """
        assert period >= 1e-4 and period <= 2.5
        if data_line is not None:
            self.write(":TRIG:OUT:PERI {0},{1}".format(data_line, period))
        else:
            self.write(":TRIG:OUT:PERI {0}".format(period))

    def get_trigger_polarity(self, data_line=None):
        """
        Query the polarity of the trigger output signal of the specified data
        line.
        """
        if data_line is not None:
            return self.ask(":TRIG:OUT:POLA? {0}".format(data_line))
        else:
            return self.ask(":TRIG:OUT:POLA?")

    def set_trigger_polarity(self, polarity="POSI", data_line=None):
        """
        Set the polarity of the trigger output signal of the specified data
        line.
        """
        assert polarity in ["POSI", "NEGA"]
        if data_line is not None:
            self.write(":TRIG:OUT:POLA {0},{1}".format(data_line, polarity))
        else:
            self.write(":TRIG:OUT:POLA {0}".format(polarity))

    def get_trigger_signal(self, data_line=None):
        """
        Query the type of the trigger output signal of the specified data line.
        """
        if data_line is not None:
            return self.ask(":TRIG:OUT:SIGN? {0}".format(data_line))
        else:
            return self.ask(":TRIG:OUT:SIGN?")

    def set_trigger_signal(self, signal="LEVEL", data_line=None):
        """
        Set the type of the trigger output signal of the specified data line.
        """
        assert signal in ["LEVEL", "SQUARE"]
        if data_line is not None:
            self.write(":TRIG:OUT:SIGN {0},{1}".format(data_line, signal))
        else:
            self.write(":TRIG:OUT:SIGN {0}".format(signal))

    def get_trigger_output_source(self, data_line=None):
        """
        Query the control source of the trigger output of the specified data
        line.
        """
        if data_line is not None:
            return self.ask(":TRIG:OUT:SOUR? {0}".format(data_line))
        else:
            return self.ask(":TRIG:OUT:SOUR?")

    def set_trigger_output_source(self, channel=1, data_line=None):
        """
        Set the control source of the trigger output of the specified data
        line.
        """
        channel = self._interpret_channel(channel)
        if data_line is not None:
            self.write(":TRIG:OUT:SOUR {0},{1}".format(data_line, channel))
        else:
            self.write(":TRIG:OUT:SOUR {0}".format(channel))

    def get_trigger_delay(self):
        """
        Query the current trigger delay.
        """
        return int(self.ask(":TRIG:DEL?"))

    def set_trigger_delay(self, delay=0):
        """
        Set the trigger delay.
        """
        assert delay >= 0 and delay <= 3600
        self.write(":TRIG:DEL {0}".format(delay))

    def get_trigger_source(self):
        """
        Query the trigger source currently selected.
        """
        return self.ask(":TRIG:SOUR?")

    def set_trigger_source(self, source="BUS"):
        """
        Select the trigger source.
        """
        assert source in ["BUS", "IMM"]
        self.write(":TRIG:SOUR {0}".format(source))
