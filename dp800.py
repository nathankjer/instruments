import re
from decimal import Decimal

import vxi11

class DP800(vxi11.Instrument):
    def __init__(self, host, *args, **kwargs):
        super(DP800, self).__init__(host, *args, **kwargs)
        idn = self.get_identification()
        match = re.match(r"RIGOL TECHNOLOGIES,DP8\d\d", idn)
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