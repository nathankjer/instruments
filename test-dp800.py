import unittest
import time
from decimal import Decimal

from dp800 import DP800

class TestDP800(unittest.TestCase):
    def setUp(self):
        self.instrument = DP800("192.168.254.101")
        self.instrument.reset()

    def tearDown(self):
        del self.instrument

    def test_analyzer(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.set_analyzer_start_time(1)
        self.instrument.set_analyzer_end_time(1)
        self.instrument.run_analyzer()

    def test_analyzer_current_time(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.set_analyzer_current_time(1)
        assert self.instrument.get_analyzer_current_time() == 1

    def test_analyzer_end_time(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.set_analyzer_end_time(1)
        assert self.instrument.get_analyzer_end_time() == 1

    def test_analyzer_file(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        assert self.instrument.get_analyzer_file() == "C:\\REC 10:RIGOL.ROF"

    def test_analyzer_unit(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.set_analyzer_unit("C")
        assert self.instrument.get_analyzer_unit() == "C"
        self.instrument.set_analyzer_unit("V")
        assert self.instrument.get_analyzer_unit() == "V"

    def test_analyzer_result(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.run_analyzer()
        self.instrument.get_analyzer_result()

    def test_analyzer_start_time(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.set_analyzer_start_time(1)
        assert self.instrument.get_analyzer_start_time() == 1

    def test_analyzer_value(self):
        self.instrument.set_record_period(1)
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        self.instrument.enable_record()
        time.sleep(1)
        self.instrument.disable_record()
        self.instrument.set_analyzer_file(10)
        self.instrument.get_analyzer_value()

    def test_channel(self):
        self.instrument.set_channel(voltage=5, current=0.001, channel=1)
        assert self.instrument.get_channel(1)["voltage"] == Decimal("5")
        assert self.instrument.get_channel(1)["current"] == Decimal("0.001")
        self.instrument.set_channel(voltage=1, current=0.005, channel=1)
        assert self.instrument.get_channel(1)["voltage"] == Decimal("1")
        assert self.instrument.get_channel(1)["current"] == Decimal("0.005")

    def test_channel_limits(self):
        self.instrument.get_channel_limits()

    def test_delay_cycles(self):
        self.instrument.set_delay_cycles("I")
        assert self.instrument.get_delay_cycles() == "I"
        self.instrument.set_delay_cycles(1)
        assert self.instrument.get_delay_cycles() == 1

    def test_delay_end_state(self):
        self.instrument.set_delay_end_state("ON")
        assert self.instrument.get_delay_end_state() == "ON"
        self.instrument.set_delay_end_state("OFF")
        assert self.instrument.get_delay_end_state() == "OFF"

    def test_delay_groups(self):
        self.instrument.set_delay_groups(2)
        assert self.instrument.get_delay_groups() == 2
        self.instrument.set_delay_groups(1)
        assert self.instrument.get_delay_groups() == 1

    def test_delay_parameters(self):
        self.instrument.set_delay_parameters(0, "ON", 1)
        assert self.instrument.get_delay_parameters(0)[0]["state"] == "ON"
        self.instrument.set_delay_parameters(0, "OFF", 1)
        assert self.instrument.get_delay_parameters(0)[0]["state"] == "OFF"

    def test_delay_state(self):
        self.instrument.enable_delay()
        assert self.instrument.delay_is_enabled()
        self.instrument.disable_delay()
        assert not self.instrument.delay_is_enabled()

    def test_delay_generation(self):
        self.instrument.set_delay_generation_pattern("10")
        assert self.instrument.get_delay_generation_pattern() == "10"
        self.instrument.set_delay_generation_pattern("01")
        assert self.instrument.get_delay_generation_pattern() == "01"

    def test_delay_stop(self):
        self.instrument.set_delay_stop_condition(">V", 2)
        assert self.instrument.get_delay_stop_condition()["condition"] == ">V"
        assert self.instrument.get_delay_stop_condition()["value"] == Decimal("2")
        self.instrument.set_delay_stop_condition("NONE")
        assert self.instrument.get_delay_stop_condition()["condition"] == "NONE"

    def test_delay_generation_time(self):
        self.instrument.set_delay_generation_time("INC", 2, 2)
        assert self.instrument.get_delay_generation_time()["mode"] == "INC"
        assert self.instrument.get_delay_generation_time()["timebase"] == 2
        assert self.instrument.get_delay_generation_time()["step"] == 2
        self.instrument.set_delay_generation_time("FIX", 1, 1)
        assert self.instrument.get_delay_generation_time()["mode"] == "FIX"

    def test_display_mode(self):
        self.instrument.set_display_mode("WAVE")
        assert self.instrument.get_display_mode() == "WAVE"
        self.instrument.set_display_mode("NORM")
        assert self.instrument.get_display_mode() == "NORM"

    def test_screen_display(self):
        self.instrument.disable_screen_display()
        assert not self.instrument.screen_display_is_enabled()
        self.instrument.enable_screen_display()
        assert self.instrument.screen_display_is_enabled()

    def test_display_text(self):
        self.instrument.set_display_text("RIGOL")
        assert self.instrument.get_display_text() == "RIGOL"
        self.instrument.clear_display_text()

    def test_clear_status(self):
        self.instrument.clear_status()

    def test_event_status_enable(self):
        self.instrument.set_event_status_enable(16)
        assert self.instrument.get_event_status_enable() == 16
        self.instrument.set_event_status_enable(0)
        assert self.instrument.get_event_status_enable() == 0

    def test_event_status(self):
        self.instrument.get_event_status()

    def test_get_identification(self):
        assert self.instrument.get_identification().startswith("RIGOL")
        assert self.instrument.get_vendor().startswith("RIGOL")
        assert self.instrument.get_product().startswith("DP8")
        assert self.instrument.get_serial_number().startswith("DP8A")
        assert self.instrument.get_firmware().startswith("00.")

    def test_busy_status(self):
        assert self.instrument.is_busy() == False

    def test_reset(self):
        self.instrument.reset()

    def test_service_request_enable(self):
        self.instrument.set_service_request_enable(16)
        self.instrument.get_service_request_enable() == 16
        self.instrument.set_service_request_enable(0)
        self.instrument.get_service_request_enable() == 0

    def test_status_byte(self):
        self.instrument.get_status_byte()

    def test_coupling_channels(self):
        self.instrument.set_coupling_channels("ALL")
        assert self.instrument.get_coupling_channels() == "ALL"
        self.instrument.set_coupling_channels("NONE")
        assert self.instrument.get_coupling_channels() == "NONE"

    def test_current_channel(self):
        self.instrument.select_channel(2)
        assert self.instrument.get_selected_channel() == 2
        self.instrument.select_channel(1)
        assert self.instrument.get_selected_channel() == 1

    def test_measure(self):
        self.instrument.measure(1)
        self.instrument.measure_current(1)
        self.instrument.measure_power(1)
        self.instrument.measure_voltage(1)

    def test_monitor(self):
        self.instrument.enable_monitor()
        assert self.instrument.monitor_is_enabled()
        self.instrument.enable_monitor_outoff()
        self.instrument.disable_monitor_outoff()
        self.instrument.enable_monitor_warning()
        self.instrument.disable_monitor_warning()
        self.instrument.enable_monitor_beeper()
        self.instrument.disable_monitor_beeper()
        self.instrument.disable_monitor()
        assert not self.instrument.monitor_is_enabled()

    def test_output_mode(self):
        self.instrument.get_output_mode()

    def test_overcurrent_protection(self):
        self.instrument.set_overcurrent_protection_value(0.01)
        self.instrument.get_overcurrent_protection_value() == 0.01
        self.instrument.enable_overcurrent_protection()
        assert self.instrument.overcurrent_protection_is_enabled()
        self.instrument.disable_overcurrent_protection()
        assert not self.instrument.overcurrent_protection_is_enabled()

    def test_overvoltage_protection(self):
        self.instrument.set_overvoltage_protection_value(1)
        self.instrument.get_overvoltage_protection_value() == 1
        self.instrument.enable_overvoltage_protection()
        assert self.instrument.overvoltage_protection_is_enabled()
        self.instrument.disable_overvoltage_protection()
        assert not self.instrument.overvoltage_protection_is_enabled()

    def test_output_range(self):
        if "DP811" in self.instrument.get_identification():
            self.instrument.set_output_range("LOW")
            assert self.instrument.get_output_range() == "LOW"
            self.instrument.set_output_range("P20V")
            assert self.instrument.get_output_range() == "P20V"

    def test_sense(self):
        idn = self.instrument.get_identification()
        if "DP821" in idn or "DP811" in idn:
            self.instrument.enable_sense()
            assert self.instrument.sense_is_enabled()
            self.instrument.disable_sense()
            assert not self.instrument.sense_is_enabled()

    def test_output(self):
        for channel in range(1, self.instrument.num_channels() + 1):
            self.instrument.select_channel(channel)
            self.instrument.enable_output()
            assert self.instrument.output_is_enabled()
            self.instrument.disable_output()
            assert not self.instrument.output_is_enabled()
            self.instrument.enable_output(channel)
            assert self.instrument.output_is_enabled(channel)
            self.instrument.disable_output()
            assert not self.instrument.output_is_enabled()
        self.instrument.select_channel(1)

    def test_tracking(self):
        idn = self.instrument.get_identification()
        if "DP82" in idn or "DP81" in idn:
            self.instrument.enable_tracking(1)
            assert self.instrument.tracking_is_enabled(1)
            self.instrument.disable_tracking(1)
            assert not self.instrument.tracking_is_enabled(1)

    def test_record_destination(self):
        self.instrument.set_record_destination("RIGOL.ROF", 10)
        assert self.instrument.get_record_destination() == "C:\\REC 10:RIGOL.ROF"

    def test_record_period(self):
        self.instrument.set_record_period(10)
        assert self.instrument.get_record_period() == 10
        self.instrument.set_record_period(1)
        assert self.instrument.get_record_period() == 1

    def test_record(self):
        self.instrument.enable_record()
        assert self.instrument.record_is_enabled()
        self.instrument.disable_record()
        assert not self.instrument.record_is_enabled()

    def test_channel_current(self):
        self.instrument.set_channel_current_increment(0.0001)
        assert self.instrument.get_channel_current_increment() == Decimal("0.0001")
        self.instrument.set_channel_current(0.0001)
        assert self.instrument.get_channel_current() == Decimal("0.0001")

    def test_channel_current_trigger(self):
        self.instrument.set_channel_current_trigger(0.001)
        assert self.instrument.get_channel_current_trigger() == Decimal("0.001")

    def test_beeper(self):
        self.instrument.beep()

    def test_brightness(self):
        self.instrument.set_brightness(100)
        assert self.instrument.get_brightness() == 100
        self.instrument.set_brightness(50)
        assert self.instrument.get_brightness() == 50

    def test_gpib_address(self):
        self.instrument.set_gpib_address(1)
        assert self.instrument.get_gpib_address() == 1
        self.instrument.set_gpib_address(2)
        assert self.instrument.get_gpib_address() == 2

    def test_lan_settings(self):
        self.instrument.enable_auto_ip()
        assert self.instrument.auto_ip_is_enabled()
        self.instrument.disable_auto_ip()
        assert not self.instrument.auto_ip_is_enabled()
        self.instrument.enable_dhcp()
        assert self.instrument.dhcp_is_enabled()
        self.instrument.disable_dhcp()
        assert not self.instrument.dhcp_is_enabled()
        self.instrument.get_mac_address()
        self.instrument.get_ip_address()
        self.instrument.get_subnet_mask()

    def test_rs232_settings(self):
        self.instrument.set_baud(9600)
        assert self.instrument.get_baud() == 9600
        self.instrument.set_data_bit(8)
        assert self.instrument.get_data_bit() == 8
        self.instrument.enable_hardware_flow_control()
        assert self.instrument.hardware_flow_control_is_enabled()
        self.instrument.disable_hardware_flow_control()
        assert not self.instrument.hardware_flow_control_is_enabled()
        self.instrument.set_parity_mode("NONE")
        assert self.instrument.get_parity_mode() == "NONE"
        self.instrument.set_stop_bit(1)
        assert self.instrument.get_stop_bit() == 1

    # TODO: Get it to pass
    # def test_contrast(self):
    #     self.instrument.set_contrast(100)
    #     assert self.instrument.get_contrast() == 100
    #     self.instrument.set_contrast(25)
    #     assert self.instrument.get_contrast() == 25

    def test_error(self):
        self.instrument.get_error()

    def test_remote_lock(self):
        self.instrument.enable_remote_lock()
        assert self.instrument.remote_lock_is_enabled()
        self.instrument.disable_remote_lock()
        assert not self.instrument.remote_lock_is_enabled()

    def test_language(self):
        self.instrument.set_language("CH")
        assert self.instrument.get_language() == "Chinese"
        self.instrument.set_language("EN")
        assert self.instrument.get_language() == "English"

    def test_lock_keyboard(self):
        self.instrument.lock_keyboard()
        assert self.instrument.keyboard_is_locked()
        self.instrument.unlock_keyboard()
        assert not self.instrument.keyboard_is_locked()

    def test_sync(self):
        self.instrument.enable_sync()
        assert self.instrument.sync_is_enabled()
        self.instrument.disable_sync()
        assert not self.instrument.sync_is_enabled()

    def test_overtemperature_protection(self):
        self.instrument.disable_overtemperature_protection()
        assert not self.instrument.overtemperature_protection_is_enabled()
        self.instrument.enable_overtemperature_protection()
        assert self.instrument.overtemperature_protection_is_enabled()

    def test_recall(self):
        self.instrument.enable_recall()
        assert self.instrument.recall_is_enabled()
        self.instrument.disable_recall()
        assert not self.instrument.recall_is_enabled()

    def test_luminosity(self):
        self.instrument.set_luminosity()

    def test_screensaver(self):
        self.instrument.enable_screen_saver()
        assert self.instrument.screen_saver_is_enabled()
        self.instrument.disable_screen_saver()
        assert not self.instrument.screen_saver_is_enabled()

    def test_top_board(self):
        assert self.instrument.top_board_is_passing()

    def test_bottom_board(self):
        assert self.instrument.bottom_board_is_passing()

    def test_fan(self):
        assert self.instrument.fan_is_passing()

    def test_temperature(self):
        temperature = self.instrument.get_temperature()
        assert temperature >= 0 and temperature <= 40

    def test_track_mode(self):
        self.instrument.set_track_mode("SYNC")
        assert self.instrument.get_track_mode() == "SYNC"

    def test_system_version(self):
        self.instrument.get_system_version()

    def test_timer_cycles(self):
        self.instrument.set_timer_cycles(10)
        assert self.instrument.get_timer_cycles() == 10
        self.instrument.set_timer_cycles("I")
        assert self.instrument.get_timer_cycles() == "I"

    def test_timer_end_state(self):
        self.instrument.set_timer_end_state("LAST")
        assert self.instrument.get_timer_end_state() == "LAST"
        self.instrument.set_timer_end_state("OFF")
        assert self.instrument.get_timer_end_state() == "OFF"

    def test_timer_groups(self):
        self.instrument.set_timer_groups(2048)
        assert self.instrument.get_timer_groups() == 2048
        self.instrument.set_timer_groups(10)
        assert self.instrument.get_timer_groups() == 10

    def test_timer(self):
        self.instrument.enable_timer()
        assert self.instrument.timer_is_enabled()
        self.instrument.disable_timer()
        assert not self.instrument.timer_is_enabled()

    def test_reconstruct_timer(self):
        self.instrument.reconstruct_timer()

    def test_timer_exp_fall_rate(self):
        self.instrument.set_timer_exp_fall_rate(1)
        assert self.instrument.get_timer_exp_fall_rate() == 1
        self.instrument.set_timer_exp_fall_rate(0)
        assert self.instrument.get_timer_exp_fall_rate() == 0

    def test_timer_interval(self):
        self.instrument.set_timer_interval(10)
        assert self.instrument.get_timer_interval() == 10
        self.instrument.set_timer_interval(1)
        assert self.instrument.get_timer_interval() == 1

    def test_timer_invert(self):
        self.instrument.enable_timer_invert()
        assert self.instrument.timer_is_inverted()
        self.instrument.disable_timer_invert()
        assert not self.instrument.timer_is_inverted()

    def test_timer_values(self):
        self.instrument.set_timer_max_value(1)
        assert self.instrument.get_timer_max_value() == Decimal("1")
        self.instrument.set_timer_min_value(1)
        assert self.instrument.get_timer_min_value() == Decimal("1")

    def test_timer_unit(self):
        self.instrument.set_timer_unit("C", 0)
        assert self.instrument.get_timer_unit() == "C,0.000"
        self.instrument.set_timer_unit("V", 0)
        assert self.instrument.get_timer_unit() == "V,0.0000"

    def test_timer_pulse_period(self):
        self.instrument.set_timer_pulse_period(100)
        assert self.instrument.get_timer_pulse_period() == 100
        self.instrument.set_timer_pulse_period(10)
        assert self.instrument.get_timer_pulse_period() == 10

    def test_timer_points(self):
        self.instrument.set_timer_points(100)
        assert self.instrument.get_timer_points() == 100
        self.instrument.set_timer_points(10)
        assert self.instrument.get_timer_points() == 10

    def test_timer_exp_rise_rate(self):
        self.instrument.set_timer_exp_rise_rate(1)
        assert self.instrument.get_timer_exp_rise_rate() == 1
        self.instrument.set_timer_exp_rise_rate(0)
        assert self.instrument.get_timer_exp_rise_rate() == 0

    def test_timer_template(self):
        self.instrument.set_timer_template("UP")
        assert self.instrument.get_timer_template() == "UP"
        self.instrument.set_timer_template("SINE")
        assert self.instrument.get_timer_template() == "SINE"

    def test_timer_ramp_symmetry(self):
        self.instrument.set_timer_ramp_symmetry(90)
        assert self.instrument.get_timer_ramp_symmetry() == 90
        self.instrument.set_timer_ramp_symmetry(50)
        assert self.instrument.get_timer_ramp_symmetry() == 50

    def test_timer_pulse_width(self):
        self.instrument.set_timer_pulse_width(9)
        assert self.instrument.get_timer_pulse_width() == 9
        self.instrument.set_timer_pulse_width(5)
        assert self.instrument.get_timer_pulse_width() == 5

    def test_trigger_source_type(self):
        self.instrument.set_trigger_source_type("IMM")
        assert self.instrument.get_trigger_source_type() == "IMM"
        self.instrument.set_trigger_source_type("BUS")
        assert self.instrument.get_trigger_source_type() == "BUS"

    def test_trigger_current(self):
        self.instrument.set_trigger_current(0.001)

    def test_trigger_input(self):
        self.instrument.enable_trigger_input()
        assert self.instrument.trigger_input_is_enabled()
        self.instrument.disable_trigger_input()
        assert not self.instrument.trigger_input_is_enabled()

    def test_trigger_response(self):
        self.instrument.set_trigger_response("ON")
        assert self.instrument.get_trigger_response() == "ON"
        self.instrument.set_trigger_response("OFF")
        assert self.instrument.get_trigger_response() == "OFF"

    def test_trigger_sensitivity(self):
        self.instrument.set_trigger_sensitivity("MID")
        assert self.instrument.get_trigger_sensitivity() == "MID"
        self.instrument.set_trigger_sensitivity("LOW")
        assert self.instrument.get_trigger_sensitivity() == "LOW"

    def test_trigger_input_source(self):
        self.instrument.set_trigger_input_source(2)
        assert self.instrument.get_trigger_input_source() == "CH2"
        self.instrument.set_trigger_input_source(1)
        assert self.instrument.get_trigger_input_source() == "CH1"

    def test_trigger_type(self):
        self.instrument.set_trigger_type("FALL")
        assert self.instrument.get_trigger_type() == "FALL"
        self.instrument.set_trigger_type("RISE")
        assert self.instrument.get_trigger_type() == "RISE"

    def test_trigger_voltage(self):
        self.instrument.set_trigger_voltage(0, 1)

    def test_trigger_condition(self):
        self.instrument.set_trigger_condition(">V", 0)
        assert self.instrument.get_trigger_condition() == ">V,0.000"

    def test_trigger_duty_cycle(self):
        self.instrument.set_trigger_duty_cycle(90)
        assert self.instrument.get_trigger_duty_cycle() == 90
        self.instrument.set_trigger_duty_cycle(50)
        assert self.instrument.get_trigger_duty_cycle() == 50

    def test_trigger_output(self):
        self.instrument.enable_trigger_output()
        assert self.instrument.trigger_output_is_enabled()
        self.instrument.disable_trigger_output()
        assert not self.instrument.trigger_output_is_enabled()

    def test_trigger_period(self):
        self.instrument.set_trigger_period(1)
        assert self.instrument.get_trigger_period() == Decimal("1")

    def test_trigger_polarity(self):
        self.instrument.set_trigger_polarity("NEGA")
        assert self.instrument.get_trigger_polarity() == "NEGATIVE"
        self.instrument.set_trigger_polarity("POSI")
        assert self.instrument.get_trigger_polarity() == "POSITIVE"

    def test_trigger_signal(self):
        self.instrument.set_trigger_signal("SQUARE")
        assert self.instrument.get_trigger_signal() == "SQUARE"
        self.instrument.set_trigger_signal("LEVEL")
        assert self.instrument.get_trigger_signal() == "LEVEL"

    def test_trigger_output_source(self):
        self.instrument.set_trigger_output_source(2)
        assert self.instrument.get_trigger_output_source() == "CH2"
        self.instrument.set_trigger_output_source(1)
        assert self.instrument.get_trigger_output_source() == "CH1"

    def test_trigger_delay(self):
        self.instrument.set_trigger_delay(1)
        assert self.instrument.get_trigger_delay() == 1
        self.instrument.set_trigger_delay(0)
        assert self.instrument.get_trigger_delay() == 0

    def test_trigger_source(self):
        self.instrument.set_trigger_source("IMM")
        assert self.instrument.get_trigger_source() == "IMM"
        self.instrument.set_trigger_source("BUS")
        assert self.instrument.get_trigger_source() == "BUS"

if __name__ == '__main__':
    unittest.main()
