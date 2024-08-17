import unittest
import time
from decimal import Decimal

from instruments import DS1000Z, DP800

class TestDS1000Z(unittest.TestCase):
    def setUp(self):
        self.instrument = DS1000Z("192.168.254.100")
        self.instrument.reset()
        self.instrument.hide_channel(1)
        self.instrument.set_probe_ratio(1, 1)
        self.instrument.set_probe_ratio(1, 2)
        self.instrument.set_probe_ratio(1, 3)
        self.instrument.set_probe_ratio(1, 4)
        self.instrument.set_channel_scale(1, 1)
        self.instrument.set_channel_scale(1, 2)
        self.instrument.set_channel_scale(1, 3)
        self.instrument.set_channel_scale(1, 4)

    def tearDown(self):
        del self.instrument

    def test_autoscale(self):
        self.instrument.show_channel()
        self.instrument.enable_source()

        self.instrument.set_source_function("SIN")
        self.instrument.set_source_frequency(41)
        self.instrument.set_source_amplitude(21e-3)
        self.instrument.set_source_amplitude(20e-3)

        self.instrument.set_channel_scale(0.01)
        self.instrument.set_timebase_scale(5e-9)
        self.instrument.autoscale()
        assert self.instrument.get_channel_scale() == 5e-3
        assert self.instrument.get_timebase_scale() == 5e-3

        self.instrument.disable_source()
        self.instrument.hide_channel()

    def test_run(self):
        self.instrument.stop()
        self.instrument.run()
        assert self.instrument.is_running()

    def test_stop(self):
        self.instrument.run()
        self.instrument.stop()
        self.instrument.run()

    def test_clear(self):
        self.instrument.stop()
        self.instrument.clear()
        self.instrument.run()

    def test_averages(self):
        for i in range(1, 10)[::-1]:
            self.instrument.set_averages(2 ** i)
            assert self.instrument.get_averages() == 2 ** i

    def test_memory_depth(self):
        for num_channels, base in [(1, 12), (2, 6), (4, 3)]:
            for channel in range(1, num_channels + 1):
                self.instrument.show_channel(channel)
            for exp in range(3, 7):
                memory_depth = int(base * 10 ** exp)
                self.instrument.set_memory_depth(memory_depth)
                assert self.instrument.get_memory_depth() == memory_depth
            for channel in range(1, num_channels + 1):
                self.instrument.hide_channel(channel)
        self.instrument.set_memory_depth("AUTO")
        assert self.instrument.get_memory_depth() == "AUTO"

    def test_acquisition_type(self):
        for acquisition_type in ["AVER", "PEAK", "HRES", "NORM"]:
            self.instrument.set_acquisition_type(acquisition_type)
            self.instrument.get_acquisition_type() == acquisition_type

    def test_sample_rate(self):
        for num_channels in [1, 2, 4]:
            for channel in range(1, num_channels + 1):
                self.instrument.show_channel(channel)
            assert self.instrument.get_sample_rate() == 1e9 / num_channels
            for channel in range(1, num_channels + 1):
                self.instrument.hide_channel(channel)

    # TODO: Calibration functions

    def test_bandwidth_limit(self):
        self.instrument.set_bandwidth_limit("20M")
        assert self.instrument.get_bandwidth_limit() == "20M"
        self.instrument.set_bandwidth_limit("OFF")
        assert self.instrument.get_bandwidth_limit() == "OFF"

    def test_coupling(self):
        for coupling in ["GND", "AC", "DC"]:
            self.instrument.set_channel_coupling(coupling)
            assert self.instrument.get_channel_coupling() == coupling

    def test_channel_display(self):
        for channel in range(1, 5):
            self.instrument.show_channel(channel)
            assert self.instrument.channel_is_shown(channel)
            assert self.instrument.num_channels_shown() == 1
            self.instrument.hide_channel(channel)
            assert not self.instrument.channel_is_shown(channel)

    def test_channel_invert(self):
        self.instrument.invert_channel()
        assert self.instrument.channel_is_inverted()
        self.instrument.uninvert_channel()
        assert not self.instrument.channel_is_inverted()

    def test_channel_offset(self):
        self.instrument.set_channel_offset(0.01)
        assert self.instrument.get_channel_offset() == 0.01
        self.instrument.set_channel_offset(0.0)
        assert self.instrument.get_channel_offset() == 0.0

    def test_channel_range(self):
        self.instrument.set_channel_range(0.8)
        assert self.instrument.get_channel_range() == 0.8
        self.instrument.set_channel_range(8)
        assert self.instrument.get_channel_range() == 8

    def test_calibration_time(self):
        self.instrument.set_calibration_time(20e-9)
        assert self.instrument.get_calibration_time() == 20e-9
        self.instrument.set_calibration_time(0)
        assert self.instrument.get_calibration_time() == 0

    def test_channel_scale(self):
        self.instrument.set_channel_scale(10)
        assert self.instrument.get_channel_scale() == 10
        self.instrument.set_channel_scale(1)
        assert self.instrument.get_channel_scale() == 1

    def test_probe_ratio(self):
        self.instrument.set_probe_ratio(10)
        assert self.instrument.get_probe_ratio() == 10
        self.instrument.set_probe_ratio(1)
        assert self.instrument.get_probe_ratio() == 1

    def test_channel_unit(self):
        self.instrument.set_channel_unit("WATT")
        self.instrument.get_channel_unit() == "WATT"
        self.instrument.set_channel_unit("VOLT")
        self.instrument.get_channel_unit() == "VOLT"

    def test_vernier(self):
        self.instrument.enable_vernier()
        assert self.instrument.vernier_is_enabled()
        self.instrument.disable_vernier()
        assert not self.instrument.vernier_is_enabled()

    def test_cursor_mode(self):
        self.instrument.set_cursor_mode("MAN")
        assert self.instrument.get_cursor_mode() == "MAN"
        self.instrument.set_cursor_mode("OFF")
        assert self.instrument.get_cursor_mode() == "OFF"

    def test_cursor_type(self):
        self.instrument.set_cursor_mode("MAN")
        self.instrument.set_cursor_type("Y")
        assert self.instrument.get_cursor_type() == "Y"
        self.instrument.set_cursor_type("X")
        assert self.instrument.get_cursor_type() == "X"
        self.instrument.set_cursor_mode("OFF")

    def test_cursor_source(self):
        self.instrument.show_channel(1)
        self.instrument.show_channel(2)
        self.instrument.set_cursor_mode("MAN")
        for channel in ["CHAN1", "CHAN2"]:
            self.instrument.set_cursor_source(channel)
            assert self.instrument.get_cursor_source() == channel
        self.instrument.set_cursor_mode("TRAC")
        for channel in ["CHAN1", "CHAN2"]:
            self.instrument.set_cursor_source(channel, 1)
            assert self.instrument.get_cursor_source(1) == channel
        self.instrument.set_cursor_mode("OFF")
        self.instrument.hide_channel(2)
        self.instrument.hide_channel(1)

    def test_cursor_time_unit(self):
        self.instrument.set_cursor_mode("MAN")
        self.instrument.set_cursor_time_unit("HZ")
        assert self.instrument.get_cursor_time_unit() == "HZ"
        self.instrument.set_cursor_time_unit("S")
        assert self.instrument.get_cursor_time_unit() == "S"
        self.instrument.set_cursor_mode("OFF")

    def test_cursor_vertical_unit(self):
        self.instrument.set_cursor_mode("MAN")
        self.instrument.set_cursor_vertical_unit("PERC")
        assert self.instrument.get_cursor_vertical_unit() == "PERC"
        self.instrument.set_cursor_vertical_unit("SOUR")
        assert self.instrument.get_cursor_vertical_unit() == "SOUR"
        self.instrument.set_cursor_mode("OFF")

    def test_cursor_position(self):
        self.instrument.set_cursor_mode("MAN")
        self.instrument.set_cursor_position("A", "X", 200)
        self.instrument.get_cursor_position("A", "X") == 200
        self.instrument.set_cursor_position("A", "X", 100)
        self.instrument.get_cursor_position("A", "X") == 100
        self.instrument.set_cursor_position("A", "Y", 200)
        self.instrument.get_cursor_position("A", "Y") == 200
        self.instrument.set_cursor_position("A", "Y", 100)
        self.instrument.get_cursor_position("A", "Y") == 100
        self.instrument.set_cursor_position("B", "X", 200)
        self.instrument.get_cursor_position("B", "X") == 200
        self.instrument.set_cursor_position("B", "X", 100)
        self.instrument.get_cursor_position("B", "X") == 100
        self.instrument.set_cursor_position("B", "Y", 200)
        self.instrument.get_cursor_position("B", "Y") == 200
        self.instrument.set_cursor_position("B", "Y", 100)
        self.instrument.get_cursor_position("B", "Y") == 100
        self.instrument.set_cursor_mode("TRAC")
        self.instrument.set_cursor_position("A", "X", 200)
        self.instrument.get_cursor_position("A", "X") == 200
        self.instrument.set_cursor_position("A", "X", 100)
        self.instrument.get_cursor_position("A", "X") == 100
        self.instrument.set_cursor_position("B", "X", 200)
        self.instrument.get_cursor_position("B", "X") == 200
        self.instrument.set_cursor_position("B", "X", 100)
        self.instrument.get_cursor_position("B", "X") == 100
        self.instrument.set_timebase_mode("XY")
        self.instrument.set_cursor_mode("XY")
        self.instrument.set_cursor_position("A", "X", 200)
        self.instrument.get_cursor_position("A", "X") == 200
        self.instrument.set_cursor_position("A", "X", 100)
        self.instrument.get_cursor_position("A", "X") == 100
        self.instrument.set_cursor_position("A", "Y", 200)
        self.instrument.get_cursor_position("A", "Y") == 200
        self.instrument.set_cursor_position("A", "Y", 100)
        self.instrument.get_cursor_position("A", "Y") == 100
        self.instrument.set_cursor_position("B", "X", 200)
        self.instrument.get_cursor_position("B", "X") == 200
        self.instrument.set_cursor_position("B", "X", 100)
        self.instrument.get_cursor_position("B", "X") == 100
        self.instrument.set_cursor_position("B", "Y", 200)
        self.instrument.get_cursor_position("B", "Y") == 200
        self.instrument.set_cursor_position("B", "Y", 100)
        self.instrument.get_cursor_position("B", "Y") == 100
        self.instrument.set_timebase_mode("MAIN")
        self.instrument.set_cursor_mode("OFF")
        self.instrument.hide_channel(1)

    def test_cursor_value(self):
        self.instrument.set_cursor_mode("MAN")
        assert self.instrument.get_cursor_value("A", "X") == -4e-6
        assert self.instrument.get_cursor_value("A", "Y") == 2
        assert self.instrument.get_cursor_value("B", "X") == 4e-6
        assert self.instrument.get_cursor_value("B", "Y") == -2
        self.instrument.set_cursor_mode("TRAC")
        assert self.instrument.get_cursor_value("A", "X") == -4e-6
        assert self.instrument.get_cursor_value("A", "Y") == None
        assert self.instrument.get_cursor_value("B", "X") == 4e-6
        assert self.instrument.get_cursor_value("B", "Y") == None
        self.instrument.set_timebase_mode("XY")
        self.instrument.set_cursor_mode("XY")
        assert self.instrument.get_cursor_value("A", "X") == 2
        assert self.instrument.get_cursor_value("A", "Y") == 2
        assert self.instrument.get_cursor_value("B", "X") == -2
        assert self.instrument.get_cursor_value("B", "Y") == -2
        self.instrument.set_timebase_mode("MAIN")
        self.instrument.set_cursor_mode("OFF")
        self.instrument.hide_channel(1)

    def test_cursor_delta(self):
        self.instrument.set_cursor_mode("MAN")
        assert self.instrument.get_cursor_delta("X") == 8e-6
        assert self.instrument.get_cursor_delta("Y") == -4
        self.instrument.set_cursor_mode("TRAC")
        assert self.instrument.get_cursor_delta("X") == 8e-6
        assert self.instrument.get_cursor_delta("Y") == None
        self.instrument.set_cursor_mode("OFF")

    def test_cursor_inverse_delta(self):
        self.instrument.set_cursor_mode("MAN")
        assert self.instrument.get_cursor_inverse_delta() == 125000
        self.instrument.set_cursor_mode("TRAC")
        assert self.instrument.get_cursor_inverse_delta() == 125000
        self.instrument.set_cursor_mode("OFF")

    def test_auto_cursor(self):
        self.instrument.show_channel(1)
        self.instrument.enable_source(1)
        self.instrument.autoscale()
        self.instrument.show_measurement("FREQ")
        self.instrument.show_measurement("PER")
        self.instrument.set_cursor_mode("AUTO")
        self.instrument.set_cursor_auto_parameters("ITEM1")
        assert self.instrument.get_cursor_auto_parameters() == "ITEM1"
        self.instrument.set_cursor_auto_parameters("ITEM2")
        assert self.instrument.get_cursor_auto_parameters() == "ITEM2"
        self.instrument.set_cursor_mode("OFF")
        self.instrument.disable_source(1)
        self.instrument.hide_channel(1)

    def test_take_screenshot(self):
        self.instrument.take_screenshot()

    def test_display_type(self):
        self.instrument.set_display_type("DOTS")
        assert self.instrument.get_display_type() == "DOTS"
        self.instrument.set_display_type("VECT")
        assert self.instrument.get_display_type() == "VECT"

    def test_persistence_time(self):
        self.instrument.set_persistence_time(1)
        assert self.instrument.get_persistence_time() == 1
        self.instrument.set_persistence_time("INF")
        assert self.instrument.get_persistence_time() == "INF"
        self.instrument.set_persistence_time("MIN")
        assert self.instrument.get_persistence_time() == "MIN"

    def test_waveform_brightness(self):
        self.instrument.set_waveform_brightness(0)
        assert self.instrument.get_waveform_brightness() == 0
        self.instrument.set_waveform_brightness(100)
        assert self.instrument.get_waveform_brightness() == 100
        self.instrument.set_waveform_brightness(50)
        assert self.instrument.get_waveform_brightness() == 50

    def test_grid(self):
        self.instrument.set_grid("NONE")
        assert self.instrument.get_grid() == "NONE"
        self.instrument.set_grid("HALF")
        assert self.instrument.get_grid() == "HALF"
        self.instrument.set_grid("FULL")
        assert self.instrument.get_grid() == "FULL"

    def test_grid_brightness(self):
        self.instrument.set_grid_brightness(0)
        assert self.instrument.get_grid_brightness() == 0
        self.instrument.set_grid_brightness(100)
        assert self.instrument.get_grid_brightness() == 100
        self.instrument.set_grid_brightness(50)
        assert self.instrument.get_grid_brightness() == 50

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
        assert self.instrument.get_product().startswith("DS10")
        assert self.instrument.get_serial_number().startswith("DS1Z")
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

    def test_self_test(self):
        assert self.instrument.self_test_is_passing() is True

    def test_wait(self):
        self.instrument.wait()

    def test_math(self):
        self.instrument.show_math()
        assert self.instrument.math_is_shown()
        self.instrument.hide_math()
        assert not self.instrument.math_is_shown()

    def test_math_operator(self):
        self.instrument.set_math_operator("SUBT")
        self.instrument.get_math_operator() == "SUBT"
        self.instrument.set_math_operator("ADD")
        self.instrument.get_math_operator() == "ADD"

    def test_math_source(self):
        self.instrument.set_math_source(1, 2)
        self.instrument.get_math_source(1) == "CHAN2"
        self.instrument.set_math_source(1, 1)
        self.instrument.get_math_source(1) == "CHAN1"
        self.instrument.set_math_source(2, 2)
        self.instrument.get_math_source(2) == "CHAN2"
        self.instrument.set_math_source(2, 1)
        self.instrument.get_math_source(2) == "CHAN1"

    def test_math_scale(self):
        self.instrument.set_math_scale(10)
        self.instrument.get_math_scale() == 10
        self.instrument.set_math_scale(1)
        self.instrument.get_math_scale() == 1

    def test_math_offset(self):
        self.instrument.set_math_offset(1)
        self.instrument.get_math_offset() == 1
        self.instrument.set_math_offset(0)
        self.instrument.get_math_offset() == 0

    def test_invert_math(self):
        self.instrument.invert_math()
        assert self.instrument.math_is_inverted()
        self.instrument.uninvert_math()
        assert not self.instrument.math_is_inverted()

    def test_reset_math(self):
        self.instrument.reset_math()

    def test_fft_window(self):
        for window in ["BLAC", "HANN", "HAMM", "FLAT", "TRI", "RECT"]:
            self.instrument.set_fft_window(window)
            assert self.instrument.get_fft_window() == window

    def test_fft_split(self):
        self.instrument.enable_fft_split()
        assert self.instrument.fft_split_is_enabled()
        self.instrument.disable_fft_split()
        assert not self.instrument.fft_split_is_enabled()

    def test_fft_unit(self):
        self.instrument.set_fft_unit("VRMS")
        self.instrument.get_fft_unit() == "VRMS"
        self.instrument.set_fft_unit("DB")
        self.instrument.get_fft_unit() == "DB"

    def test_fft_horizontal_scale(self):
        self.instrument.set_fft_horizontal_scale(5e5)
        assert self.instrument.get_fft_horizontal_scale() == 5e5
        self.instrument.set_fft_horizontal_scale(5e6)
        assert self.instrument.get_fft_horizontal_scale() == 5e6

    def test_fft_center_frequency(self):
        self.instrument.set_fft_center_frequency(1000)
        assert self.instrument.get_fft_center_frequency() == 1000

    def test_math_start(self):
        self.instrument.set_math_start(600)
        assert self.instrument.get_math_start() == 600
        self.instrument.set_math_start(0)
        assert self.instrument.get_math_start() == 0

    def test_math_end(self):
        self.instrument.set_math_end(600)
        assert self.instrument.get_math_end() == 600
        self.instrument.set_math_end(1199)
        assert self.instrument.get_math_end() == 1199

    def test_math_sensitivity(self):
        self.instrument.set_math_operator("AND")
        self.instrument.set_math_sensitivity(0.48)
        assert self.instrument.get_math_sensitivity() == 0.48
        self.instrument.set_math_sensitivity(0)
        assert self.instrument.get_math_sensitivity() == 0

    def test_differential_smoothing_width(self):
        self.instrument.enable_source(1)
        self.instrument.enable_source(2)
        self.instrument.show_channel(1)
        self.instrument.show_channel(2)
        self.instrument.autoscale()
        self.instrument.set_math_operator("DIFF")
        self.instrument.show_math()
        self.instrument.set_differential_smoothing_width(100)
        time.sleep(3)
        assert self.instrument.get_differential_smoothing_width() == 100
        self.instrument.set_differential_smoothing_width(3)
        assert self.instrument.get_differential_smoothing_width() == 3
        self.instrument.hide_math()
        self.instrument.hide_channel(2)
        self.instrument.hide_channel(1)
        self.instrument.disable_source(2)
        self.instrument.disable_source(1)

    def test_math_autoscale(self):
        self.instrument.enable_math_autoscale()
        assert self.instrument.math_autoscale_is_enabled()
        self.instrument.disable_math_autoscale()
        assert not self.instrument.math_autoscale_is_enabled()

    # TODO: FIX test_math_threshold
    # def test_math_threshold(self):
    #     for bus in [1,2]:
    #         self.instrument.show_channel(bus)
    #         self.instrument.set_source_function('SQU',bus)
    #         self.instrument.set_source_frequency(1e3,bus)
    #         self.instrument.enable_source(bus)
    #     self.instrument.autoscale()
    #     self.instrument.show_math()
    #     self.instrument.set_math_operator('AND')
    #     # Set math source not working for digital inputs
    #     self.instrument.set_math_source(1,1)
    #     self.instrument.set_math_source(2,2)
    #     self.instrument.set_math_threshold(2)
    #     assert self.instrument.get_math_threshold() == 2
    #     self.instrument.set_math_threshold(0)
    #     assert self.instrument.get_math_threshold() == 0
    #     for bus in [1,2]:
    #         self.instrument.hide_channel(bus)
    #         self.instrument.disable_source(bus)

    def test_enable_mask(self):
        self.instrument.show_channel()
        self.instrument.enable_source()
        self.instrument.enable_mask()
        assert self.instrument.mask_is_enabled()
        self.instrument.disable_mask()
        assert not self.instrument.mask_is_enabled()
        self.instrument.disable_source()
        self.instrument.hide_channel()

    def test_mask_source(self):
        for bus in [1, 2]:
            self.instrument.show_channel(bus)
            self.instrument.enable_source(bus)
        self.instrument.enable_mask()
        self.instrument.set_mask_source(2)
        assert self.instrument.get_mask_source() == "CHAN2"
        self.instrument.set_mask_source(1)
        assert self.instrument.get_mask_source() == "CHAN1"
        self.instrument.disable_mask()
        for bus in [1, 2]:
            self.instrument.hide_channel(bus)
            self.instrument.disable_source(bus)

    def test_run_mask(self):
        self.instrument.show_channel()
        self.instrument.enable_source()
        self.instrument.enable_mask()
        self.instrument.run_mask()
        assert self.instrument.mask_is_running()
        self.instrument.stop_mask()
        assert not self.instrument.mask_is_running()
        self.instrument.disable_mask()
        self.instrument.disable_source()
        self.instrument.hide_channel()

    def test_mask_stats(self):
        self.instrument.show_channel()
        self.instrument.enable_source()
        self.instrument.enable_mask()
        self.instrument.show_mask_stats()
        assert self.instrument.mask_stats_is_shown()
        self.instrument.hide_mask_stats()
        assert not self.instrument.mask_stats_is_shown()
        self.instrument.disable_mask()
        self.instrument.disable_source()
        self.instrument.hide_channel()

    def test_mask_stop_on_fail(self):
        self.instrument.enable_mask_stop_on_fail()
        assert self.instrument.mask_stop_on_fail_is_enabled()
        self.instrument.disable_mask_stop_on_fail()
        assert not self.instrument.mask_stop_on_fail_is_enabled()

    def test_mask_beeper(self):
        self.instrument.enable_mask_beeper()
        assert self.instrument.mask_beeper_is_enabled()
        self.instrument.disable_mask_beeper()
        assert not self.instrument.mask_beeper_is_enabled()

    def test_mask_adjustment(self):
        self.instrument.set_mask_adjustment("X", 1)
        assert self.instrument.get_mask_adjustment("X") == 1
        self.instrument.set_mask_adjustment("X", 0.24)
        assert self.instrument.get_mask_adjustment("X") == 0.24

    def test_create_mask(self):
        self.instrument.show_channel()
        self.instrument.enable_source()
        self.instrument.enable_mask()
        self.instrument.create_mask()
        self.instrument.disable_mask()
        self.instrument.disable_source()
        self.instrument.hide_channel()

    def test_mask_frames(self):
        assert type(self.instrument.get_passed_mask_frames()) == int
        assert type(self.instrument.get_failed_mask_frames()) == int
        assert type(self.instrument.get_total_mask_frames()) == int

    def test_reset_mask(self):
        self.instrument.reset_mask()

    def test_measurement_source(self):
        self.instrument.set_measurement_source(2)
        assert self.instrument.get_measurement_source() == "CHAN2"
        self.instrument.set_measurement_source(1)
        assert self.instrument.get_measurement_source() == "CHAN1"

    def test_counter_source(self):
        self.instrument.set_counter_source(2)
        assert self.instrument.get_counter_source() == "CHAN2"
        self.instrument.set_counter_source(1)
        assert self.instrument.get_counter_source() == "CHAN1"

    def test_clear_measurement(self):
        self.instrument.show_measurement("VMAX")
        self.instrument.clear_measurement(1)
        self.instrument.recover_measurement(1)
        self.instrument.clear_measurement(1)

    def test_all_measurements_display(self):
        time.sleep(3)
        self.instrument.show_all_measurements_display()
        assert self.instrument.all_measurements_is_shown()
        self.instrument.hide_all_measurements_display()
        assert not self.instrument.all_measurements_is_shown()

    def test_all_measurements_display_source(self):
        self.instrument.set_all_measurements_display_source(2)
        assert self.instrument.get_all_measurements_display_source() == "CHAN2"
        self.instrument.set_all_measurements_display_source(1)
        assert self.instrument.get_all_measurements_display_source() == "CHAN1"

    def test_measure_threshold(self):
        self.instrument.set_measure_threshold_max(60)
        assert self.instrument.get_measure_threshold_max() == 60
        self.instrument.set_measure_threshold_max(90)
        assert self.instrument.get_measure_threshold_max() == 90
        self.instrument.set_measure_threshold_mid(20)
        assert self.instrument.get_measure_threshold_mid() == 20
        self.instrument.set_measure_threshold_mid(50)
        assert self.instrument.get_measure_threshold_mid() == 50
        self.instrument.set_measure_threshold_min(5)
        assert self.instrument.get_measure_threshold_min() == 5
        self.instrument.set_measure_threshold_min(10)
        assert self.instrument.get_measure_threshold_min() == 10

    def test_measure_phase_source(self):
        self.instrument.set_measure_phase_source(2)
        assert self.instrument.get_measure_phase_source() == "CHAN2"
        self.instrument.set_measure_phase_source(1)
        assert self.instrument.get_measure_phase_source() == "CHAN1"

    def test_measure_delay_source(self):
        self.instrument.set_measure_delay_source(2)
        assert self.instrument.get_measure_delay_source() == "CHAN2"
        self.instrument.set_measure_delay_source(1)
        assert self.instrument.get_measure_delay_source() == "CHAN1"

    def test_show_statistics(self):
        self.instrument.show_measurement("VMAX")
        self.instrument.hide_statistics()
        assert not self.instrument.statistic_is_shown()
        self.instrument.show_statistics()
        assert self.instrument.statistic_is_shown()
        self.instrument.clear_measurement()
        self.instrument.hide_channel()
        self.instrument.disable_source()

    def test_statistic_mode(self):
        self.instrument.set_statistic_mode("DIFF")
        assert self.instrument.get_statistic_mode() == "DIFF"
        self.instrument.set_statistic_mode("EXTR")
        assert self.instrument.get_statistic_mode() == "EXTR"

    def test_reset_statistic(self):
        self.instrument.reset_statistic()

    def test_get_measurement(self):
        assert type(self.instrument.get_measurement("VMAX")) == float
        self.instrument.clear_measurement()

    def test_enable_show_reference(self):
        self.instrument.show_reference()
        assert self.instrument.reference_is_shown()
        self.instrument.hide_reference()
        assert not self.instrument.reference_is_shown()

    def test_enable_reference(self):
        self.instrument.enable_reference()
        assert self.instrument.reference_is_enabled()
        self.instrument.disable_reference()
        assert not self.instrument.reference_is_enabled()

    def test_reference_source(self):
        self.instrument.show_channel()
        self.instrument.set_reference_source(1)
        assert self.instrument.get_reference_source() == "CHAN1"
        self.instrument.hide_channel()

    def test_reference_scale(self):
        self.instrument.show_channel()
        self.instrument.show_reference()
        self.instrument.enable_reference()
        self.instrument.set_reference_scale(0.1)
        assert self.instrument.get_reference_scale() == 0.1
        self.instrument.reset_reference()
        self.instrument.disable_reference()
        self.instrument.hide_reference()
        self.instrument.hide_channel()

    def test_reference_offset(self):
        self.instrument.show_channel()
        self.instrument.show_reference()
        self.instrument.enable_reference()
        self.instrument.set_reference_offset(0.0)
        assert self.instrument.get_reference_offset() == 0.0
        self.instrument.reset_reference()
        self.instrument.disable_reference()
        self.instrument.hide_reference()
        self.instrument.hide_channel()

    def test_enable_source(self):
        self.instrument.enable_source()
        assert self.instrument.source_is_enabled()
        self.instrument.disable_source()
        assert not self.instrument.source_is_enabled()

    def test_source_impedance(self):
        self.instrument.set_source_impedance("OMEG")
        self.instrument.get_source_impedance() == "OMEG"
        self.instrument.set_source_impedance("FIFT")
        self.instrument.get_source_impedance() == "FIFT"

    def test_source_frequency(self):
        self.instrument.set_source_frequency(1e3)
        assert self.instrument.get_source_frequency() == 1e3
        self.instrument.set_source_frequency(1e5)
        assert self.instrument.get_source_frequency() == 1e5

    def test_source_phase(self):
        self.instrument.set_source_phase(90)
        self.instrument.get_source_phase() == 90
        self.instrument.set_source_phase(0)
        self.instrument.get_source_phase() == 0

    def test_align_source_phases(self):
        for bus in [1, 2]:
            self.instrument.show_channel(bus)
            self.instrument.enable_source(bus)
        self.instrument.autoscale()
        self.instrument.align_source_phases()
        for bus in [1, 2]:
            self.instrument.hide_channel(bus)
            self.instrument.disable_source(bus)

    def test_source_function(self):
        self.instrument.set_source_function("SQU")
        self.instrument.get_source_function() == "SQU"
        self.instrument.set_source_function("SIN")
        self.instrument.get_source_function() == "SIN"

    def test_source_ramp_symmetry(self):
        self.instrument.set_source_ramp_symmetry(50)
        assert self.instrument.get_source_ramp_symmetry() == 50
        self.instrument.set_source_ramp_symmetry(10)
        assert self.instrument.get_source_ramp_symmetry() == 10

    def test_source_amplitude(self):
        self.instrument.set_source_amplitude(0.1)
        assert self.instrument.get_source_amplitude() == 0.1
        self.instrument.set_source_amplitude(1)
        assert self.instrument.get_source_amplitude() == 1

    def test_source_offset(self):
        self.instrument.set_source_offset(0)
        assert self.instrument.get_source_offset() == 0

    def test_source_duty_cycle(self):
        self.instrument.set_source_duty_cycle(90)
        assert self.instrument.get_source_duty_cycle() == 90
        self.instrument.set_source_duty_cycle(20)
        assert self.instrument.get_source_duty_cycle() == 20

    def test_source_modulation(self):
        self.instrument.enable_source_modulation()
        assert self.instrument.source_modulation_is_enabled()
        self.instrument.disable_source_modulation()
        assert not self.instrument.source_modulation_is_enabled()

    def test_source_modulation_type(self):
        self.instrument.set_source_modulation_type("FM")
        assert self.instrument.get_source_modulation_type() == "FM"
        self.instrument.set_source_modulation_type("AM")
        assert self.instrument.get_source_modulation_type() == "AM"

    def test_source_modulation_depth(self):
        self.instrument.set_source_modulation_depth(120)
        assert self.instrument.get_source_modulation_depth() == 120
        self.instrument.set_source_modulation_depth(100)
        assert self.instrument.get_source_modulation_depth() == 100

    def test_source_modulation_frequency(self):
        self.instrument.set_source_modulation_frequency(100)
        assert self.instrument.get_source_modulation_frequency() == 100
        self.instrument.set_source_modulation_frequency(1000)
        assert self.instrument.get_source_modulation_frequency() == 1000

    def test_source_modulation_function(self):
        self.instrument.set_source_modulation_function("SQU")
        assert self.instrument.get_source_modulation_function() == "SQU"
        self.instrument.set_source_modulation_function("SIN")
        assert self.instrument.get_source_modulation_function() == "SIN"

    def test_source_modulation_deviation(self):
        self.instrument.set_source_modulation_type("FM")
        self.instrument.set_source_modulation_deviation(10)
        self.instrument.get_source_modulation_deviation() == 10

    def test_source_configuration(self):
        assert self.instrument.get_source_configuration().count(",") == 4

    def test_configure_source(self):
        self.instrument.configure_source()

    def test_disable_autoscale(self):
        self.instrument.disable_manual_autoscale()
        assert not self.instrument.manual_autoscale_is_enabled()
        self.instrument.enable_manual_autoscale()
        assert self.instrument.manual_autoscale_is_enabled()

    def test_beeper(self):
        self.instrument.enable_beeper()
        assert self.instrument.beeper_is_enabled()
        self.instrument.disable_beeper()
        assert not self.instrument.beeper_is_enabled()

    def test_error_message(self):
        assert self.instrument.get_error_message() == '0,"No error"'

    def test_gpib(self):
        self.instrument.set_gpib(2)
        assert self.instrument.get_gpib() == 2
        self.instrument.set_gpib(1)
        assert self.instrument.get_gpib() == 1

    def test_language(self):
        self.instrument.set_language("SCH")
        assert self.instrument.get_language() == "SCH"
        self.instrument.set_language("ENGL")
        assert self.instrument.get_language() == "ENGL"

    def test_lock_keyboard(self):
        self.instrument.lock_keyboard()
        assert self.instrument.keyboard_is_locked()
        self.instrument.unlock_keyboard()
        assert not self.instrument.keyboard_is_locked()

    def test_recall(self):
        self.instrument.enable_recall()
        assert self.instrument.recall_is_enabled()
        self.instrument.disable_recall()
        assert not self.instrument.recall_is_enabled()

    def test_timebase_delay(self):
        self.instrument.enable_timebase_delay()
        assert self.instrument.timebase_delay_is_enabled()
        self.instrument.disable_timebase_delay()
        assert not self.instrument.timebase_delay_is_enabled()

    def test_timebase_delay_offset(self):
        self.instrument.enable_timebase_delay()
        self.instrument.set_timebase_delay_offset(1e-6)
        assert self.instrument.get_timebase_delay_offset() == 1e-6
        self.instrument.set_timebase_delay_offset(0)
        assert self.instrument.get_timebase_delay_offset() == 0
        self.instrument.disable_timebase_delay()

    def test_timebase_delay_scale(self):
        self.instrument.enable_timebase_delay()
        self.instrument.set_timebase_delay_scale(1e-6)
        assert self.instrument.get_timebase_delay_scale() == 1e-6
        self.instrument.set_timebase_delay_scale(5e-7)
        assert self.instrument.get_timebase_delay_scale() == 5e-7
        self.instrument.disable_timebase_delay()

    def test_timebase_offset(self):
        self.instrument.set_timebase_offset(1)
        assert self.instrument.get_timebase_offset() == 1
        self.instrument.set_timebase_offset(0)
        assert self.instrument.get_timebase_offset() == 0

    def test_timebase_scale(self):
        self.instrument.set_timebase_scale(200e-3)
        assert self.instrument.get_timebase_scale() == 200e-3
        self.instrument.set_timebase_scale(1e-6)
        assert self.instrument.get_timebase_scale() == 1e-6

    def test_timebase_mode(self):
        self.instrument.set_timebase_mode("ROLL")
        assert self.instrument.get_timebase_mode() == "ROLL"
        self.instrument.set_timebase_mode("XY")
        assert self.instrument.get_timebase_mode() == "XY"
        self.instrument.set_timebase_mode("MAIN")
        assert self.instrument.get_timebase_mode() == "MAIN"

    def test_trigger_mode(self):
        for mode in [
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
        ]:
            self.instrument.set_trigger_mode(mode)
            assert self.instrument.get_trigger_mode() == mode

    def test_trigger_coupling(self):
        for coupling in ["AC", "LFR", "HFR", "DC"]:
            self.instrument.set_trigger_coupling(coupling)
            assert self.instrument.get_trigger_coupling() == coupling

    def test_trigger_status(self):
        assert self.instrument.get_trigger_status() in [
            "TD",
            "WAIT",
            "RUN",
            "AUTO",
            "STOP",
        ]
        assert self.instrument.is_running()
        self.instrument.set_trigger_sweep("SING")
        self.instrument.force_trigger()
        assert not self.instrument.is_running()
        self.instrument.set_trigger_sweep("AUTO")
        self.instrument.run()

    def test_trigger_sweep(self):
        self.instrument.set_trigger_sweep("NORM")
        assert self.instrument.get_trigger_sweep() == "NORM"
        self.instrument.set_trigger_sweep("SING")
        assert self.instrument.get_trigger_sweep() == "SING"
        self.instrument.set_trigger_sweep("AUTO")
        assert self.instrument.get_trigger_sweep() == "AUTO"

    def test_trigger_holdoff(self):
        self.instrument.set_trigger_holdoff(10)
        assert self.instrument.get_trigger_holdoff() == 10
        self.instrument.set_trigger_holdoff(16e-9)
        assert self.instrument.get_trigger_holdoff() == 16e-9

    def test_trigger_noise_reject(self):
        self.instrument.enable_trigger_noise_reject()
        assert self.instrument.trigger_noise_reject_is_enabled()
        self.instrument.disable_trigger_noise_reject()
        assert not self.instrument.trigger_noise_reject_is_enabled()

    def test_trigger_source(self):
        self.instrument.set_trigger_source(2)
        assert self.instrument.get_trigger_source() == "CHAN2"
        self.instrument.set_trigger_source(1)
        assert self.instrument.get_trigger_source() == "CHAN1"

    def test_trigger_direction(self):
        self.instrument.set_trigger_mode("VID")
        for slope in ["POS", "NEG"]:
            self.instrument.set_trigger_direction(slope)
            assert self.instrument.get_trigger_direction() == slope
        self.instrument.set_trigger_mode("EDGE")
        for slope in ["POS", "NEG", "RFAL"]:
            self.instrument.set_trigger_direction(slope)
            assert self.instrument.get_trigger_direction() == slope

    def test_trigger_level(self):
        for mode in ["VID", "PULS", "EDGE"]:
            self.instrument.set_trigger_mode(mode)
            self.instrument.set_trigger_level(1)
            assert self.instrument.get_trigger_level() == 1
            self.instrument.set_trigger_level(0)
            assert self.instrument.get_trigger_level() == 0

    def test_trigger_condition(self):
        self.instrument.set_trigger_mode("PULS")
        self.instrument.set_trigger_condition("PLES")
        assert self.instrument.get_trigger_condition() == "PLES"
        self.instrument.set_trigger_condition("PGR")
        assert self.instrument.get_trigger_condition() == "PGR"

    def test_trigger_width(self):
        self.instrument.set_trigger_mode("PULS")
        self.instrument.set_trigger_condition("PGL")
        self.instrument.set_trigger_width(1e-3)
        self.instrument.get_trigger_width() == 1e-3
        self.instrument.set_trigger_width(1e-6)
        self.instrument.get_trigger_width() == 1e-6
        self.instrument.set_trigger_lower_width(1e-7)
        assert self.instrument.get_trigger_lower_width() == 1e-7
        self.instrument.set_trigger_lower_width(2e-7)
        assert self.instrument.get_trigger_lower_width() == 2e-7
        self.instrument.set_trigger_upper_width(5e-7)
        assert self.instrument.get_trigger_upper_width() == 5e-7
        self.instrument.set_trigger_upper_width(1e-6)
        assert self.instrument.get_trigger_upper_width() == 1e-6

    def test_trigger_window(self):
        self.instrument.set_trigger_mode("SLOP")
        self.instrument.set_trigger_window("TB")
        assert self.instrument.get_trigger_window() == "TB"
        self.instrument.set_trigger_window("TA")
        assert self.instrument.get_trigger_window() == "TA"

    def test_trigger_sync_type(self):
        self.instrument.set_trigger_mode("VID")
        self.instrument.set_trigger_sync_type("ODDF")
        assert self.instrument.get_trigger_sync_type() == "ODDF"
        self.instrument.set_trigger_sync_type("ALIN")
        assert self.instrument.get_trigger_sync_type() == "ALIN"

    def test_trigger_line(self):
        self.instrument.set_trigger_mode("VID")
        self.instrument.set_trigger_line(250)
        assert self.instrument.get_trigger_line() == 250
        self.instrument.set_trigger_line(1)
        assert self.instrument.get_trigger_line() == 1

    def test_trigger_standard(self):
        self.instrument.set_trigger_mode("VID")
        self.instrument.set_trigger_standard("PALS")
        assert self.instrument.get_trigger_standard() == "PALS"
        self.instrument.set_trigger_standard("NTSC")
        assert self.instrument.get_trigger_standard() == "NTSC"

    def test_trigger_pattern(self):
        self.instrument.set_trigger_mode("PATT")
        self.instrument.set_trigger_pattern("L,L,L,L")
        assert self.instrument.get_trigger_pattern() == "L,L,L,L"
        self.instrument.set_trigger_pattern("X,X,X,X")
        assert self.instrument.get_trigger_pattern() == "X,X,X,X"

    def test_waveform_source(self):
        self.instrument.set_waveform_source(2)
        assert self.instrument.get_waveform_source() == "CHAN2"
        self.instrument.set_waveform_source(1)
        assert self.instrument.get_waveform_source() == "CHAN1"

    def test_waveform_mode(self):
        for mode in ["MAX", "RAW", "NORM"]:
            self.instrument.set_waveform_mode(mode)
            assert self.instrument.get_waveform_mode() == mode

    def test_waveform_format(self):
        for format in ["WORD", "ASC", "BYTE"]:
            self.instrument.set_waveform_format(format)
            assert self.instrument.get_waveform_format() == format

    def test_waveform_data(self):
        self.instrument.set_waveform_format("ASC")
        assert self.instrument.get_waveform_data().startswith(b"#90000")

    def test_waveform_increment(self):
        assert type(self.instrument.get_waveform_increment("X")) == float
        assert type(self.instrument.get_waveform_increment("Y")) == float

    def test_waveform_origin(self):
        assert type(self.instrument.get_waveform_origin("X")) == float
        assert type(self.instrument.get_waveform_origin("Y")) == float

    def test_waveform_reference(self):
        assert type(self.instrument.get_waveform_reference("X"))
        assert type(self.instrument.get_waveform_reference("Y"))

    def test_waveform_start(self):
        self.instrument.set_waveform_start(600)
        assert self.instrument.get_waveform_start() == 600
        self.instrument.set_waveform_start(1)
        assert self.instrument.get_waveform_start() == 1

    def test_waveform_stop(self):
        self.instrument.set_waveform_stop(600)
        assert self.instrument.get_waveform_stop() == 600
        self.instrument.set_waveform_stop(1200)
        assert self.instrument.get_waveform_stop() == 1200

    def test_waveform_preamble(self):
        assert len(self.instrument.get_waveform_preamble()) == 10


    def test_get_waveform_samples(self):
        self.instrument.set_probe_ratio(1)
        self.instrument.show_channel()
        self.instrument.set_channel_scale(1)
        self.instrument.set_channel_offset(0)
        self.instrument.set_timebase_scale(5e-6)
        self.instrument.set_source_function('RAMP')
        self.instrument.set_source_frequency(50e3)
        self.instrument.set_source_amplitude(5)
        self.instrument.enable_source()
        time.sleep(1)
        x_axis, samples = self.instrument.get_waveform_samples(channel=1, mode='RAW')
        self.assertTrue(len(samples) > 0, "Waveform samples should not be empty")
        self.assertEqual(len(x_axis), len(samples), "X-axis and samples should have the same length")
        for sample in samples:
            self.assertTrue(-10 <= sample <= 10, "Sample out of expected voltage range")
        x_diff = [x_axis[i+1] - x_axis[i] for i in range(len(x_axis)-1)]
        self.assertAlmostEqual(sum(x_diff) / len(x_diff), x_diff[0], places=9, msg="X-axis values should increment uniformly")


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
