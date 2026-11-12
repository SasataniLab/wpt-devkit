"""Tests pinning the numbers used in the WPT TX design notes (pytest)."""

import pytest

import hrtim_calc as hc

F_NEW = 169.5e6      # PLLM /8, PLLN x113, PLLR /2 from 24 MHz
F_OLD = 170.0e6      # PLLM /6, PLLN x85,  PLLR /2
F_PWM = 6.78e6


# ---- clock, tick, limits --------------------------------------------------

def test_tick_and_thrtim():
    assert hc.tick_ns(F_NEW) == pytest.approx(0.184366, abs=1e-6)
    assert hc.t_hrtim_ns(F_NEW) == pytest.approx(5.899705, abs=1e-6)
    # RM0440 Table 231 quotes 184 ps at 170 MHz
    assert round(hc.tick_ns(F_OLD) * 1e3) == 184


def test_prescaler_scales_tick():
    assert hc.tick_ns(F_OLD, 5) == pytest.approx(5.882353, abs=1e-6)   # Table 231: 5.88 ns
    assert hc.tick_ns(F_OLD, 7) == pytest.approx(23.529412, abs=1e-6)  # Table 231: 23.53 ns


def test_limits_table_232():
    assert [hc.min_compare(c) for c in range(6)] == [0x60, 0x30, 0x18, 0x0C, 0x06, 0x03]
    assert [hc.max_period(c) for c in range(6)] == [0xFFDF, 0xFFEF, 0xFFF7, 0xFFFB, 0xFFFD, 0xFFFD]
    assert hc.ticks_to_ns(F_NEW, hc.min_compare()) == pytest.approx(17.699, abs=1e-3)


def test_fhrtim_above_170mhz_rejected():
    with pytest.raises(ValueError):
        hc.tick_ns(170.5e6)


def test_min_pwm_frequency_table_231():
    # 83.0 kHz at 170 MHz, CKPSC 0
    assert hc.frequency_for_period(F_OLD, 0xFFDF) == pytest.approx(83.05e3, rel=1e-3)


# ---- frequency <-> period -------------------------------------------------

def test_period_169p5_is_exact():
    p = hc.period_for_frequency(F_NEW, F_PWM)
    assert p.per == 800
    assert p.frequency_hz == 6.78e6
    assert p.error_hz == 0.0
    assert p.exact


def test_period_170_is_off_by_3khz():
    p = hc.period_for_frequency(F_OLD, F_PWM)
    assert p.per == 802
    assert p.frequency_hz == pytest.approx(6_783_042.39, abs=0.01)
    assert p.error_hz == pytest.approx(3042.39, abs=0.01)
    assert p.error_ppm == pytest.approx(448.7, abs=0.1)
    assert not p.exact


def test_period_170_neighbour():
    assert hc.frequency_for_period(F_OLD, 803) == pytest.approx(6_774_595.27, abs=0.01)


def test_reachable_frequencies_in_ism_band():
    got = hc.reachable_frequencies(F_NEW, F_PWM, 15e3)
    assert [per for per, _ in got] == [799, 800, 801]
    assert got[0][1] == pytest.approx(6_788_485.61, abs=0.01)
    assert got[1][1] == 6.78e6
    assert got[2][1] == pytest.approx(6_771_535.58, abs=0.01)


def test_frequency_step_is_about_8p5_khz():
    got = dict(hc.reachable_frequencies(F_NEW, F_PWM, 15e3))
    assert got[799] - got[800] == pytest.approx(8485.6, abs=0.1)
    assert got[800] - got[801] == pytest.approx(8464.4, abs=0.1)


def test_period_out_of_range():
    with pytest.raises(ValueError):
        hc.period_for_frequency(F_NEW, 100e6)      # would need PER = 54
    with pytest.raises(ValueError):
        hc.period_for_frequency(F_NEW, 10e3)       # would need PER > 0xFFDF


# ---- restriction checks ---------------------------------------------------

def test_check_period():
    assert hc.check_period(800) == 800
    with pytest.raises(ValueError):
        hc.check_period(0x5F)
    with pytest.raises(ValueError):
        hc.check_period(0xFFE0)
    with pytest.raises(ValueError):
        hc.check_period(0xBF, half_mode=True)       # HALF mode needs 6 fHRTIM periods
    assert hc.check_period(0xC0, half_mode=True) == 0xC0


def test_check_compare():
    assert hc.check_compare(96, 800) == 96
    assert hc.check_compare(800, 800) == 800
    with pytest.raises(ValueError):
        hc.check_compare(95, 800)
    with pytest.raises(ValueError):
        hc.check_compare(801, 800)
    with pytest.raises(ValueError):
        hc.check_compare(0, 800)
    assert hc.check_compare(0, 800, allow_zero=True) == 0
    with pytest.raises(ValueError):
        hc.check_compare(800, 800, allow_equal_period=False)


# ---- duty and phase -------------------------------------------------------

def test_duty_and_phase():
    assert hc.duty_to_compare(800, 0.5) == 400
    assert hc.phase_to_ticks(800, 180.0) == 400
    assert hc.phase_to_ticks(800, 90.0) == 200
    assert hc.phase_to_ticks(800, 360.0) == 0
    assert hc.ticks_to_phase_deg(800, 96) == pytest.approx(43.2)
    with pytest.raises(ValueError):
        hc.duty_to_compare(800, 0.1)                # 80 ticks: below the 96-tick minimum


def test_ns_tick_conversion():
    assert hc.ns_to_ticks(F_NEW, 8.0) == 43
    assert hc.ns_to_ticks(F_NEW, 10.0) == 54
    assert hc.ticks_to_ns(F_NEW, 800) == pytest.approx(147.4926, abs=1e-4)


# ---- dead-time unit -------------------------------------------------------

def test_deadtime_step():
    assert hc.t_dtg_ns(F_NEW) == pytest.approx(0.737463, abs=1e-6)
    assert hc.t_dtg_ns(F_OLD) == pytest.approx(0.735294, abs=1e-6)       # "735 ps"
    assert hc.t_dtg_ns(F_OLD, 7) == pytest.approx(94.1176, abs=1e-4)     # Table 237


def test_deadtime_8_and_10_ns():
    d = hc.deadtime_fields(F_NEW, 8.0, 10.0)
    assert (d.dtprsc, d.dtr, d.dtf, d.sdtr, d.sdtf) == (0, 11, 14, 0, 0)
    assert d.rise_ns == pytest.approx(8.112, abs=1e-3)
    assert d.fall_ns == pytest.approx(10.324, abs=1e-3)
    assert d.rise_error_ns == pytest.approx(0.112, abs=1e-3)
    assert d.fall_error_ns == pytest.approx(0.324, abs=1e-3)
    assert d.register == 0x000E000B


def test_deadtime_bringup_value():
    d = hc.deadtime_fields(F_NEW, 20.0, 20.0)
    assert d.dtr == d.dtf == 27
    assert d.rise_ns == pytest.approx(19.912, abs=1e-3)


def test_deadtime_sign_lock_bits():
    d = hc.deadtime_fields(F_NEW, 8.0, 10.0, lock_sign=True)
    assert d.register == 0x000E000B | (1 << 14) | (1 << 30)


def test_deadtime_negative_sets_sign():
    d = hc.deadtime_fields(F_NEW, -2.0, 8.0)
    assert (d.dtr, d.sdtr, d.sdtf) == (3, 1, 0)
    assert d.rise_ns == pytest.approx(-2.212, abs=1e-3)
    assert d.register & (1 << 9)


def test_deadtime_prescaler_selection():
    assert hc.deadtime_fields(F_NEW, 376.0, 376.0).dtprsc == 0       # 510 steps
    d = hc.deadtime_fields(F_NEW, 500.0, 8.0)
    assert d.dtprsc == 1
    assert d.dtr == 339
    assert d.dtf == 5                                               # 7.37 ns: coarser step
    assert (d.register >> 10) & 0x7 == 1


def test_deadtime_too_large():
    with pytest.raises(ValueError):
        hc.deadtime_fields(F_NEW, 60_000.0, 8.0)
    with pytest.raises(ValueError):
        hc.deadtime_fields(F_NEW, 500.0, 8.0, dtprsc=0)


# ---- four-compare method --------------------------------------------------

def test_leg_compares_basic():
    leg = hc.leg_compares(800, 96, 44, 54)
    assert leg.values == (140, 496, 550, 96)
    assert hc.verify_leg(800, *leg.values) == (44, 54)
    assert hc.ticks_to_ns(F_NEW, 44) == pytest.approx(8.112, abs=1e-3)
    assert hc.ticks_to_ns(F_NEW, 54) == pytest.approx(9.956, abs=1e-3)


def test_leg_compares_forbidden_zone():
    with pytest.raises(ValueError):
        hc.leg_compares(800, 0, 44, 54)        # out2 reset at tick 0
    with pytest.raises(ValueError):
        hc.leg_compares(800, 360, 44, 54)      # out2 set wraps to tick 14
    with pytest.raises(ValueError):
        hc.leg_compares(800, 450, 44, 54)      # out1 reset wraps to tick 50


def test_verify_leg_detects_overlap():
    with pytest.raises(ValueError):
        hc.verify_leg(800, 140, 560, 550, 96)  # out2 turns on before out1 turns off
    with pytest.raises(ValueError):
        hc.verify_leg(800, 140, 496, 496, 96)  # zero dead time
    assert hc.verify_leg(800, 140, 496, 497, 96) == (44, 1)


def test_verify_leg_rejects_narrow_pulse():
    with pytest.raises(ValueError):
        hc.verify_leg(800, 100, 150, 200, 700)  # out1 pulse of 50 ticks < 96


def test_full_bridge_180_degrees():
    a, b = hc.full_bridge_compares(800, 400, 44, 54)
    assert a.values == (140, 496, 550, 96)
    assert b.values == (540, 96, 150, 496)
    assert (b.start - a.start) % 800 == 400
    for v in a.values + b.values:
        assert 96 <= v <= 799


def test_full_bridge_every_phase_is_reachable():
    for phase in range(800):
        a, b = hc.full_bridge_compares(800, phase, 44, 54)
        assert (b.start - a.start) % 800 == phase
        assert hc.verify_leg(800, *a.values) == (44, 54)
        assert hc.verify_leg(800, *b.values) == (44, 54)


def test_full_bridge_needs_both_legs_to_move():
    # with leg A pinned at its lowest offset, part of the phase range is lost
    lost = 0
    for phase in range(800):
        try:
            hc.leg_compares(800, 96 + phase, 44, 54)
        except ValueError:
            lost += 1
    assert lost == 290


def test_summary_runs():
    text = hc.summary()
    assert "PER               800" in text
    assert "6780000.00 Hz" in text
