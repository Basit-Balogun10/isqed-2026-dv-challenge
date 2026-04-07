import os
import json
import random
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

from testbench.agents.tl_ul_driver import TlUlDriver


RND_SEED = 20240221

REG_INTR_STATE = 0x00
REG_INTR_ENABLE = 0x04
REG_INTR_TEST = 0x08
REG_DATA_IN = 0x0C
REG_DIRECT_OUT = 0x10
REG_MASKED_OUT_LOWER = 0x14
REG_MASKED_OUT_UPPER = 0x18
REG_DIRECT_OE = 0x1C
REG_MASKED_OE_LOWER = 0x20
REG_MASKED_OE_UPPER = 0x24
REG_INTR_CTRL_EN_RISING = 0x28
REG_INTR_CTRL_EN_FALLING = 0x2C
REG_INTR_CTRL_EN_LVLHIGH = 0x30
REG_INTR_CTRL_EN_LVLLOW = 0x34

FUNC_COV_ENV = "AUTOVERIFIER_FUNC_COV_FILE"


def _int(v):
    try:
        return int(v)
    except Exception:
        return int(v.value)


def _mask32(v):
    return v & 0xFFFFFFFF


def _bitmask(width):
    return (1 << width) - 1 if width > 0 else 0


def _get_gpio_width(dut):
    candidates = []
    for name in ["gpio_i", "gpio_o", "gpio_oe_o", "cio_gpio_i", "cio_gpio_o", "cio_gpio_en_o"]:
        if hasattr(dut, name):
            try:
                candidates.append(len(getattr(dut, name)))
            except Exception:
                try:
                    candidates.append(int(getattr(dut, name).value.n_bits))
                except Exception:
                    pass
    if candidates:
        return max(candidates)
    return 32


def _find_input_signal(dut):
    for name in ["gpio_i", "cio_gpio_i"]:
        if hasattr(dut, name):
            return getattr(dut, name)
    return None


def _find_intr_signal(dut):
    for name in ["intr_gpio_o", "intr_o", "gpio_intr_o", "interrupt_o"]:
        if hasattr(dut, name):
            return getattr(dut, name)
    return None


def _find_clk(dut):
    for name in ["clk_i", "clk", "clock"]:
        if hasattr(dut, name):
            return getattr(dut, name)
    raise AttributeError("No clock found")


def _find_reset(dut):
    for name in ["rst_ni", "reset_n", "rst_n"]:
        if hasattr(dut, name):
            return getattr(dut, name)
    raise AttributeError("No active-low reset found")


async def _reset_dut(dut, clk, rst_n, gpio_in_sig, width):
    if gpio_in_sig is not None:
        gpio_in_sig.value = 0
    rst_n.value = 0
    for _ in range(5):
        await RisingEdge(clk)
    rst_n.value = 1
    for _ in range(5):
        await RisingEdge(clk)
    if gpio_in_sig is not None:
        gpio_in_sig.value = 0
    for _ in range(3):
        await RisingEdge(clk)


async def _tl_write(driver, addr, data):
    await driver.write(addr, _mask32(data))


async def _tl_read(driver, addr):
    val = await driver.read(addr)
    return _mask32(_int(val))


def _mk_cov():
    return {
        "test_name": "test_repair_iteration_2_1",
        "seed": RND_SEED,
        "bins": {
            "intr_test_write": 0,
            "direct_out_write": 0,
            "direct_oe_write": 0,
            "masked_out_lower_write": 0,
            "masked_out_upper_write": 0,
            "masked_oe_lower_write": 0,
            "masked_oe_upper_write": 0,
            "rising_only_irq": 0,
            "falling_only_irq": 0,
            "level_high_irq": 0,
            "level_low_irq": 0,
            "mixed_mode_same_pin": 0,
            "w1c_clear": 0,
            "level_reassert_after_clear": 0,
            "multi_pin_activity": 0,
            "data_in_observed_low": 0,
            "data_in_observed_high": 0,
            "interrupt_output_seen_low": 0,
            "interrupt_output_seen_high": 0,
            "enable_masking_checked": 0
        }
    }


def _hit(cov, name):
    cov["bins"][name] = 1


def _write_cov(cov):
    path = os.getenv(FUNC_COV_ENV, "autoverifier_func_cov.json")
    total = len(cov["bins"])
    hit = sum(1 for v in cov["bins"].values() if v)
    payload = {
        "format": "AUTOVERIFIER_FUNC_COV_FILE",
        "test_name": cov["test_name"],
        "seed": cov["seed"],
        "functional_bins_total": total,
        "functional_bins_hit": hit,
        "functional_percent": (100.0 * hit / total) if total else 100.0,
        "bins": cov["bins"],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


async def _wait_sync_latency(clk, cycles=4):
    for _ in range(cycles):
        await RisingEdge(clk)


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    random.seed(RND_SEED)
    cov = _mk_cov()

    clk = _find_clk(dut)
    rst_n = _find_reset(dut)
    gpio_in_sig = _find_input_signal(dut)
    intr_sig = _find_intr_signal(dut)
    width = _get_gpio_width(dut)
    active_width = min(width, 16)
    full_mask = _bitmask(active_width)

    cocotb.start_soon(Clock(clk, 10, units="ns").start())

    driver = TlUlDriver(dut)

    try:
        await _reset_dut(dut, clk, rst_n, gpio_in_sig, active_width)

        await _tl_write(driver, REG_INTR_ENABLE, 0)
        await _tl_write(driver, REG_INTR_CTRL_EN_RISING, 0)
        await _tl_write(driver, REG_INTR_CTRL_EN_FALLING, 0)
        await _tl_write(driver, REG_INTR_CTRL_EN_LVLHIGH, 0)
        await _tl_write(driver, REG_INTR_CTRL_EN_LVLLOW, 0)
        await _tl_write(driver, REG_INTR_STATE, 0xFFFFFFFF)

        val = await _tl_read(driver, REG_DATA_IN)
        if (val & full_mask) == 0:
            _hit(cov, "data_in_observed_low")

        await _tl_write(driver, REG_DIRECT_OUT, 0xA5A5A5A5)
        _hit(cov, "direct_out_write")
        await _tl_write(driver, REG_DIRECT_OE, 0x5A5A5A5A)
        _hit(cov, "direct_oe_write")

        lower_mask = 0x000F
        lower_data = 0x0005
        await _tl_write(driver, REG_MASKED_OUT_LOWER, (lower_mask << 16) | lower_data)
        _hit(cov, "masked_out_lower_write")

        upper_mask = 0x000F
        upper_data = 0x000A
        await _tl_write(driver, REG_MASKED_OUT_UPPER, (upper_mask << 16) | upper_data)
        _hit(cov, "masked_out_upper_write")

        await _tl_write(driver, REG_MASKED_OE_LOWER, (0x0003 << 16) | 0x0001)
        _hit(cov, "masked_oe_lower_write")
        await _tl_write(driver, REG_MASKED_OE_UPPER, (0x0003 << 16) | 0x0002)
        _hit(cov, "masked_oe_upper_write")

        await _tl_write(driver, REG_INTR_TEST, 0x1)
        _hit(cov, "intr_test_write")
        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & 0x1) != 0, "INTR_TEST did not set interrupt state bit 0"
        await _tl_write(driver, REG_INTR_STATE, 0x1)
        _hit(cov, "w1c_clear")

        pin_rise = 0
        pin_fall = 1
        pin_lvlh = 2
        pin_lvll = 3
        pin_mixed = 4
        pin_multi_a = 5
        pin_multi_b = 6

        rising_mask = (1 << pin_rise) | (1 << pin_mixed) | (1 << pin_multi_a)
        falling_mask = (1 << pin_fall) | (1 << pin_mixed) | (1 << pin_multi_b)
        lvlhigh_mask = (1 << pin_lvlh) | (1 << pin_mixed)
        lvllow_mask = (1 << pin_lvll)

        await _tl_write(driver, REG_INTR_CTRL_EN_RISING, rising_mask)
        await _tl_write(driver, REG_INTR_CTRL_EN_FALLING, falling_mask)
        await _tl_write(driver, REG_INTR_CTRL_EN_LVLHIGH, lvlhigh_mask)
        await _tl_write(driver, REG_INTR_CTRL_EN_LVLLOW, lvllow_mask)
        await _tl_write(driver, REG_INTR_ENABLE, full_mask)

        if gpio_in_sig is not None:
            gpio_in_sig.value = 0
        await _wait_sync_latency(clk, 4)

        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & (1 << pin_lvll)) != 0, "Level-low interrupt did not assert at low input"
        _hit(cov, "level_low_irq")

        await _tl_write(driver, REG_INTR_STATE, (1 << pin_lvll))
        _hit(cov, "w1c_clear")
        await _wait_sync_latency(clk, 3)
        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & (1 << pin_lvll)) != 0, "Level-low interrupt did not reassert after W1C while condition persisted"
        _hit(cov, "level_reassert_after_clear")

        if gpio_in_sig is not None:
            gpio_in_sig.value = (1 << pin_rise) | (1 << pin_lvlh) | (1 << pin_mixed) | (1 << pin_multi_a)
        await _wait_sync_latency(clk, 4)

        din = await _tl_read(driver, REG_DATA_IN)
        if (din & ((1 << pin_rise) | (1 << pin_lvlh) | (1 << pin_mixed) | (1 << pin_multi_a))) != 0:
            _hit(cov, "data_in_observed_high")

        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & (1 << pin_rise)) != 0, "Rising-edge interrupt missing"
        assert (st & (1 << pin_lvlh)) != 0, "Level-high interrupt missing"
        assert (st & (1 << pin_mixed)) != 0, "Mixed-mode pin interrupt missing on high transition"
        _hit(cov, "rising_only_irq")
        _hit(cov, "level_high_irq")
        _hit(cov, "mixed_mode_same_pin")

        await _tl_write(driver, REG_INTR_STATE, (1 << pin_rise) | (1 << pin_lvlh) | (1 << pin_mixed))
        _hit(cov, "w1c_clear")
        await _wait_sync_latency(clk, 3)
        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & (1 << pin_lvlh)) != 0, "Level-high interrupt did not reassert after W1C while high persisted"
        _hit(cov, "level_reassert_after_clear")

        if gpio_in_sig is not None:
            gpio_in_sig.value = (1 << pin_fall) | (1 << pin_multi_b)
        await _wait_sync_latency(clk, 4)

        st = await _tl_read(driver, REG_INTR_STATE)
        assert (st & (1 << pin_fall)) != 0, "Falling-edge interrupt missing"
        assert (st & (1 << pin_mixed)) != 0, "Mixed-mode pin interrupt missing on falling/high-low transition"
        assert (st & (1 << pin_multi_a)) != 0, "Concurrent rising pin interrupt missing"
        assert (st & (1 << pin_multi_b)) != 0, "Concurrent falling pin interrupt missing"
        _hit(cov, "falling_only_irq")
        _hit(cov, "multi_pin_activity")

        await _tl_write(driver, REG_INTR_ENABLE, 0)
        await _tl_write(driver, REG_INTR_STATE, 0xFFFFFFFF)
        if gpio_in_sig is not None:
            gpio_in_sig.value = 0
        await _wait_sync_latency(clk, 2)
        if gpio_in_sig is not None:
            gpio_in_sig.value = (1 << pin_rise) | (1 << pin_lvlh)
        await _wait_sync_latency(clk, 4)
        st = await _tl_read(driver, REG_INTR_STATE)
        assert st == 0 or (st & full_mask) == 0, "Interrupt state changed while interrupts disabled"
        _hit(cov, "enable_masking_checked")

        if intr_sig is not None:
            await Timer(1, units="ns")
            intr_val = _int(intr_sig)
            if intr_val == 0:
                _hit(cov, "interrupt_output_seen_low")

        await _tl_write(driver, REG_INTR_ENABLE, full_mask)
        if gpio_in_sig is not None:
            gpio_in_sig.value = 0
        await _wait_sync_latency(clk, 4)
        if intr_sig is not None:
            await Timer(1, units="ns")
            intr_val = _int(intr_sig)
            if intr_val != 0:
                _hit(cov, "interrupt_output_seen_high")

    finally:
        _write_cov(cov)
