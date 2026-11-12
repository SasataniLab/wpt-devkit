"""HRTIM register calculator for the STM32G474 (no dependencies).

Converts physical targets (frequency, duty, phase, dead time in ns) into
HRTIM register values and checks the high-resolution restrictions.

All rules come from RM0440 Rev 9, section 28:

* counter clock fHRCK = 32 x fHRTIM / 2**CKPSC          (28.3.3, Table 231)
* PER / CMP limits per CKPSC, 3 fHRTIM periods minimum   (28.3.4, Table 232)
* tDTG = 2**DTPRSC x tHRTIM / 8, |DTx| <= 511            (28.3.4, Table 237)
* HRTIM_DTxR bit layout                                  (28.5.26)
* same-output events closer than 3 tHRTIM lose resolution (28.3.7)

The relation fPWM = fHRCK / PER is not written as a formula in RM0440; it is
read from Table 231 and should be confirmed with a frequency counter.

Run ``python hrtim_calc.py`` for a summary of the 169.5 MHz / 6.78 MHz setup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

HR_STEPS = 32                    # high-resolution steps per fHRTIM period
DT_STEPS_PER_THRTIM = 8          # dead-time generator steps per fHRTIM period
MIN_FHRTIM_PERIODS = 3           # minimum PER / CMP value, in fHRTIM periods
F_HRTIM_MAX_HZ = 170_000_000     # DS12288 Table 59
DT_FIELD_MAX = 511               # DTRx / DTFx are 9-bit fields

# RM0440 Table 232 (index = CKPSC[2:0])
PER_CMP_MIN = (0x0060, 0x0030, 0x0018, 0x000C, 0x0006, 0x0003, 0x0003, 0x0003)
PER_CMP_MAX = (0xFFDF, 0xFFEF, 0xFFF7, 0xFFFB, 0xFFFD, 0xFFFD, 0xFFFD, 0xFFFD)


# --------------------------------------------------------------------------
# clock and tick helpers
# --------------------------------------------------------------------------

def _check_ckpsc(ckpsc: int) -> None:
    if not 0 <= ckpsc <= 7:
        raise ValueError(f"CKPSC must be 0..7, got {ckpsc}")


def counter_clock_hz(f_hrtim_hz: float, ckpsc: int = 0) -> float:
    """Equivalent counter clock fHRCK / 2**CKPSC in Hz."""
    _check_ckpsc(ckpsc)
    if not 0 < f_hrtim_hz <= F_HRTIM_MAX_HZ:
        raise ValueError(f"fHRTIM must be in (0, {F_HRTIM_MAX_HZ}] Hz, got {f_hrtim_hz}")
    return f_hrtim_hz * HR_STEPS / (1 << ckpsc)


def tick_ns(f_hrtim_hz: float, ckpsc: int = 0) -> float:
    """Duration of one counter tick in ns (184.37 ps at 169.5 MHz, CKPSC 0)."""
    return 1e9 / counter_clock_hz(f_hrtim_hz, ckpsc)


def t_hrtim_ns(f_hrtim_hz: float) -> float:
    """One fHRTIM period in ns (capture resolution, synchroniser step)."""
    return 1e9 / f_hrtim_hz


def ns_to_ticks(f_hrtim_hz: float, ns: float, ckpsc: int = 0) -> int:
    """Nearest whole number of counter ticks for a time in ns."""
    return int(round(ns / tick_ns(f_hrtim_hz, ckpsc)))


def ticks_to_ns(f_hrtim_hz: float, ticks: float, ckpsc: int = 0) -> float:
    return ticks * tick_ns(f_hrtim_hz, ckpsc)


def min_compare(ckpsc: int = 0) -> int:
    """Smallest legal PER / CMP value (3 fHRTIM periods)."""
    _check_ckpsc(ckpsc)
    return PER_CMP_MIN[ckpsc]


def max_period(ckpsc: int = 0) -> int:
    """Largest legal PER / CMP value."""
    _check_ckpsc(ckpsc)
    return PER_CMP_MAX[ckpsc]


# --------------------------------------------------------------------------
# restriction checks
# --------------------------------------------------------------------------

def check_period(per: int, ckpsc: int = 0, half_mode: bool = False) -> int:
    """Validate a period register value; returns it or raises ValueError.

    In HALF mode the period must be at least 6 fHRTIM periods (RM0440 p.900).
    """
    lo = min_compare(ckpsc) * (2 if half_mode else 1)
    hi = max_period(ckpsc)
    if int(per) != per:
        raise ValueError(f"PER must be an integer, got {per}")
    if not lo <= per <= hi:
        raise ValueError(f"PER = {per} outside {lo}..{hi} for CKPSC = {ckpsc}")
    return int(per)


def check_compare(value: int, per: int, ckpsc: int = 0, allow_zero: bool = False,
                  allow_equal_period: bool = True) -> int:
    """Validate a compare register value against the high-resolution rules.

    * values 1 .. min-1 are forbidden;
    * 0 is accepted only with ``allow_zero`` (CMP1 / CMP3 null duty-cycle case);
    * a value above PER never matches.
    """
    if int(value) != value:
        raise ValueError(f"compare value must be an integer, got {value}")
    if value == 0:
        if allow_zero:
            return 0
        raise ValueError("compare value 0 is only legal for the CMP1/CMP3 null duty-cycle case")
    lo = min_compare(ckpsc)
    if value < lo:
        raise ValueError(f"compare value {value} below the minimum {lo} (3 fHRTIM periods)")
    hi = per if allow_equal_period else per - 1
    if value > hi:
        raise ValueError(f"compare value {value} above {hi} (PER = {per}): no compare match")
    return int(value)


# --------------------------------------------------------------------------
# frequency <-> period
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodResult:
    per: int
    frequency_hz: float
    error_hz: float
    error_ppm: float
    exact: bool


def frequency_for_period(f_hrtim_hz: float, per: int, ckpsc: int = 0) -> float:
    """PWM frequency produced by a period register value."""
    check_period(per, ckpsc)
    return counter_clock_hz(f_hrtim_hz, ckpsc) / per


def period_for_frequency(f_hrtim_hz: float, f_target_hz: float, ckpsc: int = 0) -> PeriodResult:
    """Period register value whose frequency is closest to the target."""
    if f_target_hz <= 0:
        raise ValueError("target frequency must be positive")
    f_ck = counter_clock_hz(f_hrtim_hz, ckpsc)
    ideal = f_ck / f_target_hz
    best: Optional[Tuple[float, int]] = None
    for cand in (int(ideal), int(ideal) + 1):
        if min_compare(ckpsc) <= cand <= max_period(ckpsc):
            err = abs(f_ck / cand - f_target_hz)
            if best is None or err < best[0]:
                best = (err, cand)
    if best is None:
        raise ValueError(f"{f_target_hz} Hz is not reachable with CKPSC = {ckpsc}")
    per = best[1]
    f_act = f_ck / per
    err = f_act - f_target_hz
    exact = abs(err) < 1e-9 * f_target_hz
    return PeriodResult(per, f_act, err, err / f_target_hz * 1e6, exact)


def reachable_frequencies(f_hrtim_hz: float, f_center_hz: float, span_hz: float,
                          ckpsc: int = 0) -> List[Tuple[int, float]]:
    """All (PER, frequency) pairs with |f - f_center| <= span, lowest PER first."""
    f_ck = counter_clock_hz(f_hrtim_hz, ckpsc)
    lo = max(min_compare(ckpsc), int(f_ck / (f_center_hz + span_hz)))
    hi = min(max_period(ckpsc), int(f_ck / max(f_center_hz - span_hz, 1e-9)) + 1)
    out = []
    for per in range(lo, hi + 1):
        f = f_ck / per
        if abs(f - f_center_hz) <= span_hz:
            out.append((per, f))
    return out


# --------------------------------------------------------------------------
# duty and phase
# --------------------------------------------------------------------------

def duty_to_compare(per: int, duty: float, ckpsc: int = 0) -> int:
    """Compare value for 'set on period, reset on compare' with the given duty."""
    if not 0.0 < duty <= 1.0:
        raise ValueError("duty must be in (0, 1]")
    return check_compare(int(round(per * duty)), per, ckpsc)


def phase_to_ticks(per: int, phase_deg: float) -> int:
    """Phase in degrees -> ticks, wrapped into 0 .. PER-1."""
    return int(round(per * (phase_deg % 360.0) / 360.0)) % per


def ticks_to_phase_deg(per: int, ticks: int) -> float:
    return 360.0 * (ticks % per) / per


# --------------------------------------------------------------------------
# dead-time unit (HRTIM_DTxR)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class DeadTime:
    dtprsc: int
    dtr: int
    dtf: int
    sdtr: int
    sdtf: int
    t_dtg_ns: float
    rise_ns: float           # achieved, signed
    fall_ns: float
    rise_error_ns: float     # achieved - requested
    fall_error_ns: float
    register: int            # HRTIM_DTxR value


def t_dtg_ns(f_hrtim_hz: float, dtprsc: int = 0) -> float:
    """Dead-time generator step: 2**DTPRSC x tHRTIM / 8, in ns."""
    if not 0 <= dtprsc <= 7:
        raise ValueError("DTPRSC must be 0..7")
    return t_hrtim_ns(f_hrtim_hz) * (1 << dtprsc) / DT_STEPS_PER_THRTIM


def deadtime_fields(f_hrtim_hz: float, rise_ns: float, fall_ns: float,
                    dtprsc: Optional[int] = None, lock_sign: bool = False) -> DeadTime:
    """Register fields for a requested rising / falling dead time in ns.

    Negative values request an overlap (sign bits). Without ``dtprsc`` the
    smallest prescaler that holds both values is used. ``lock_sign`` sets the
    write-once DTRSLK / DTFSLK bits.
    """
    candidates = range(8) if dtprsc is None else (dtprsc,)
    for prsc in candidates:
        step = t_dtg_ns(f_hrtim_hz, prsc)
        dtr = int(round(abs(rise_ns) / step))
        dtf = int(round(abs(fall_ns) / step))
        if dtr <= DT_FIELD_MAX and dtf <= DT_FIELD_MAX:
            sdtr = 1 if rise_ns < 0 and dtr else 0
            sdtf = 1 if fall_ns < 0 and dtf else 0
            got_r = -dtr * step if sdtr else dtr * step
            got_f = -dtf * step if sdtf else dtf * step
            reg = dtr | (sdtr << 9) | (prsc << 10) | (dtf << 16) | (sdtf << 25)
            if lock_sign:
                reg |= (1 << 14) | (1 << 30)
            return DeadTime(prsc, dtr, dtf, sdtr, sdtf, step, got_r, got_f,
                            got_r - rise_ns, got_f - fall_ns, reg)
    raise ValueError(f"dead time {rise_ns} / {fall_ns} ns does not fit "
                     f"(max {DT_FIELD_MAX} steps of the selected prescaler)")


# --------------------------------------------------------------------------
# four-compare complementary pair (DTEN = 0)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LegCompares:
    """Compare values for one half-bridge leg, all edges at full resolution.

    out1: set on CMP1, reset on CMP2.  out2: set on CMP3, reset on CMP4.
    ``start`` is the instant out2 turns off (reference rising edge).
    """
    per: int
    start: int
    cmp1_out1_set: int
    cmp2_out1_reset: int
    cmp3_out2_set: int
    cmp4_out2_reset: int
    dt_rise_ticks: int       # out2 off -> out1 on
    dt_fall_ticks: int       # out1 off -> out2 on

    @property
    def values(self) -> Tuple[int, int, int, int]:
        return (self.cmp1_out1_set, self.cmp2_out1_reset,
                self.cmp3_out2_set, self.cmp4_out2_reset)


def verify_leg(per: int, out1_set: int, out1_reset: int, out2_set: int, out2_reset: int,
               ckpsc: int = 0, min_dead_ticks: int = 1) -> Tuple[int, int]:
    """Check a four-compare set; returns (dt_rise, dt_fall) in ticks.

    Raises ValueError if a value violates the compare limits, if the two
    outputs would be active together, if a dead time is below
    ``min_dead_ticks``, or if a pulse or gap on one output is shorter than
    3 fHRTIM periods.
    """
    check_period(per, ckpsc)
    for v in (out1_set, out1_reset, out2_set, out2_reset):
        check_compare(v, per, ckpsc, allow_equal_period=False)
    high1 = (out1_reset - out1_set) % per
    high2 = (out2_reset - out2_set) % per
    dt_fall = (out2_set - out1_reset) % per
    dt_rise = (out1_set - out2_reset) % per
    if high1 + high2 + dt_fall + dt_rise != per:
        raise ValueError("outputs overlap: both would be active at the same time")
    if dt_fall < min_dead_ticks or dt_rise < min_dead_ticks:
        raise ValueError(f"dead time below {min_dead_ticks} ticks (rise {dt_rise}, fall {dt_fall})")
    narrow = min_compare(ckpsc)
    for name, width in (("out1 pulse", high1), ("out1 gap", per - high1),
                        ("out2 pulse", high2), ("out2 gap", per - high2)):
        if width < narrow:
            raise ValueError(f"{name} of {width} ticks is below 3 fHRTIM periods ({narrow} ticks)")
    return dt_rise, dt_fall


def leg_compares(per: int, start: int, dt_rise_ticks: int, dt_fall_ticks: int,
                 high_ticks: Optional[int] = None, ckpsc: int = 0,
                 min_dead_ticks: int = 1) -> LegCompares:
    """Four compare values for one leg.

    The reference waveform is high from ``start`` for ``high_ticks`` (default
    PER // 2). out1 turns on ``dt_rise_ticks`` after the reference rises and
    off when it falls; out2 turns on ``dt_fall_ticks`` after the reference
    falls and off when it rises. Events are taken modulo PER; an event that
    lands on 0 .. min-1 cannot be produced by a compare and raises ValueError.
    """
    check_period(per, ckpsc)
    if high_ticks is None:
        high_ticks = per // 2
    s1 = (start + dt_rise_ticks) % per
    r1 = (start + high_ticks) % per
    s2 = (start + high_ticks + dt_fall_ticks) % per
    r2 = start % per
    got_r, got_f = verify_leg(per, s1, r1, s2, r2, ckpsc, min_dead_ticks)
    if (got_r, got_f) != (dt_rise_ticks, dt_fall_ticks):
        raise ValueError("requested dead times do not fit in the period")
    return LegCompares(per, start % per, s1, r1, s2, r2, dt_rise_ticks, dt_fall_ticks)


def full_bridge_compares(per: int, phase_ticks: int, dt_rise_ticks: int, dt_fall_ticks: int,
                         high_ticks: Optional[int] = None, ckpsc: int = 0,
                         min_dead_ticks: int = 1) -> Tuple[LegCompares, LegCompares]:
    """Compare sets for two free-running timers, leg B ``phase_ticks`` after leg A.

    Both timers must share PER and be started by one write to HRTIM_MCR. The
    common offset is searched so that no edge of either leg falls into the
    forbidden 0 .. min-1 zone; the lowest usable offset is returned.
    """
    for start_a in range(min_compare(ckpsc), per):
        try:
            leg_a = leg_compares(per, start_a, dt_rise_ticks, dt_fall_ticks,
                                 high_ticks, ckpsc, min_dead_ticks)
            leg_b = leg_compares(per, start_a + phase_ticks, dt_rise_ticks, dt_fall_ticks,
                                 high_ticks, ckpsc, min_dead_ticks)
        except ValueError:
            continue
        return leg_a, leg_b
    raise ValueError(f"no offset places all edges outside the forbidden zone for phase {phase_ticks}")


# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------

def summary(f_hrtim_hz: float = 169.5e6, f_target_hz: float = 6.78e6) -> str:
    p = period_for_frequency(f_hrtim_hz, f_target_hz)
    lines = [
        f"fHRTIM            {f_hrtim_hz / 1e6:.3f} MHz, tHRTIM {t_hrtim_ns(f_hrtim_hz):.4f} ns",
        f"tick              {tick_ns(f_hrtim_hz) * 1e3:.2f} ps",
        f"PER               {p.per} -> {p.frequency_hz:.2f} Hz "
        f"(error {p.error_hz:+.2f} Hz, {p.error_ppm:+.1f} ppm)",
        f"CMP range         {min_compare()} .. {p.per} ticks "
        f"({ticks_to_ns(f_hrtim_hz, min_compare()):.2f} ns minimum)",
        f"dead-time step    {t_dtg_ns(f_hrtim_hz) * 1e3:.1f} ps",
    ]
    for target in (8.0, 10.0, 20.0):
        d = deadtime_fields(f_hrtim_hz, target, target)
        lines.append(f"dead time {target:4.1f} ns DTx = {d.dtr:3d} -> {d.rise_ns:.3f} ns "
                     f"({d.rise_error_ns:+.3f} ns)")
    lines.append("frequencies within +/-15 kHz:")
    for per, f in reachable_frequencies(f_hrtim_hz, f_target_hz, 15e3):
        lines.append(f"  PER {per}: {f:.1f} Hz")
    a, b = full_bridge_compares(p.per, p.per // 2, 44, 54)
    lines.append(f"four-compare, 180 deg, 44/54 ticks: leg A {a.values}, leg B {b.values}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
