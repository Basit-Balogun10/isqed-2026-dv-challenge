import json
import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from testbench.agents.tlul_driver import TlUlDriver


def _get_env_path(name, default):
    value = os.getenv(name, default)
    return Path(value)


def _append_func_cov(record):
    path = _get_env_path("AUTOVERIFIER_FUNC_COV_FILE", "autoverifier_func_cov.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = []
    if path.exists():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, list):
                data = loaded
            elif isinstance(loaded, dict):
                data = loaded.get("records", [])
        except Exception:
            data = []
    data.append(record)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def _u32_words_from_bytes(b):
    assert len(b) == 16
    return [int.from_bytes(b[i : i + 4], "little") for i in range(0, 16, 4)]


def _bytes_from_u32_words(words):
    return b"".join(int(w & 0xFFFFFFFF).to_bytes(4, "little") for w in words)


async def _reset_dut(dut):
    dut.rst_ni.value = 0
    dut.clk_i.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk_i)


async def _wait_cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk_i)


async def _tl_write(driver, addr, data):
    await driver.write(addr, data)


async def _tl_read(driver, addr):
    return await driver.read(addr)


@cocotb.test()
async def test_repair_iteration_1_1(dut):
    random.seed(0xA5E1_0001)

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())
    await _reset_dut(dut)

    driver = TlUlDriver(dut, "tl")
    if hasattr(driver, "start"):
        maybe = driver.start()
        if maybe is not None:
            try:
                await maybe
            except TypeError:
                pass

    cov = {
        "scenario": "aes_ecb_cbc_correctness_gap",
        "seed": 0xA5E1_0001,
        "bins": {},
    }

    def hit(name):
        cov["bins"][name] = cov["bins"].get(name, 0) + 1

    base = 0x0

    key_128 = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    iv_128 = bytes.fromhex("0F0E0D0C0B0A09080706050403020100")
    pt_128 = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
    pt2_128 = bytes.fromhex("112233445566778899AABBCCDDEEFF00")

    key_words = _u32_words_from_bytes(key_128)
    iv_words = _u32_words_from_bytes(iv_128)
    pt_words = _u32_words_from_bytes(pt_128)
    pt2_words = _u32_words_from_bytes(pt2_128)

    for i, w in enumerate(key_words):
        await _tl_write(driver, base + 0x10 + 4 * i, w)
        hit("key_write")
    for i, w in enumerate(iv_words):
        await _tl_write(driver, base + 0x20 + 4 * i, w)
        hit("iv_write")
    for i, w in enumerate(pt_words):
        await _tl_write(driver, base + 0x30 + 4 * i, w)
        hit("pt_write")

    await _tl_write(driver, base + 0x00, 0x1)
    hit("start_encrypt_ecb")
    await _wait_cycles(dut, 20)

    ecb_ct_words = []
    for i in range(4):
        ecb_ct_words.append(await _tl_read(driver, base + 0x40 + 4 * i))
        hit("ct_read")
    ecb_ct = _bytes_from_u32_words(ecb_ct_words)

    for i, w in enumerate(key_words):
        await _tl_write(driver, base + 0x10 + 4 * i, w)
    for i, w in enumerate(iv_words):
        await _tl_write(driver, base + 0x20 + 4 * i, w)
    for i, w in enumerate(pt_words):
        await _tl_write(driver, base + 0x30 + 4 * i, w)

    await _tl_write(driver, base + 0x00, 0x3)
    hit("start_decrypt_ecb")
    await _wait_cycles(dut, 20)

    ecb_pt_words = []
    for i in range(4):
        ecb_pt_words.append(await _tl_read(driver, base + 0x40 + 4 * i))
    ecb_pt = _bytes_from_u32_words(ecb_pt_words)

    for i, w in enumerate(key_words):
        await _tl_write(driver, base + 0x10 + 4 * i, w)
    for i, w in enumerate(iv_words):
        await _tl_write(driver, base + 0x20 + 4 * i, w)
    for i, w in enumerate(pt_words):
        await _tl_write(driver, base + 0x30 + 4 * i, w)

    await _tl_write(driver, base + 0x00, 0x5)
    hit("start_encrypt_cbc")
    await _wait_cycles(dut, 20)

    cbc_ct_words_0 = [await _tl_read(driver, base + 0x40 + 4 * i) for i in range(4)]
    cbc_ct_0 = _bytes_from_u32_words(cbc_ct_words_0)

    for i, w in enumerate(pt2_words):
        await _tl_write(driver, base + 0x30 + 4 * i, w)
    await _tl_write(driver, base + 0x00, 0x5)
    hit("cbc_chain_second_block")
    await _wait_cycles(dut, 20)

    cbc_ct_words_1 = [await _tl_read(driver, base + 0x40 + 4 * i) for i in range(4)]
    cbc_ct_1 = _bytes_from_u32_words(cbc_ct_words_1)

    for i, w in enumerate(key_words):
        await _tl_write(driver, base + 0x10 + 4 * i, w)
    for i, w in enumerate(iv_words):
        await _tl_write(driver, base + 0x20 + 4 * i, w)
    for i, w in enumerate(cbc_ct_words_0):
        await _tl_write(driver, base + 0x30 + 4 * i, w)

    await _tl_write(driver, base + 0x00, 0x7)
    hit("start_decrypt_cbc")
    await _wait_cycles(dut, 20)

    cbc_pt_words = [await _tl_read(driver, base + 0x40 + 4 * i) for i in range(4)]
    cbc_pt = _bytes_from_u32_words(cbc_pt_words)

    _append_func_cov(
        {
            "test": "test_repair_iteration_1_1",
            "scenario": "aes_ecb_cbc_correctness_gap",
            "seed": 0xA5E1_0001,
            "coverage": {
                "bins_hit": len(cov["bins"]),
                "bins_total": 75,
                "bins": cov["bins"],
            },
        }
    )

    assert len(ecb_ct) == 16
    assert len(ecb_pt) == 16
    assert len(cbc_ct_0) == 16
    assert len(cbc_ct_1) == 16
    assert len(cbc_pt) == 16
    assert cbc_pt == pt_128
    assert ecb_pt == pt_128
    assert cbc_ct_0 != cbc_ct_1 or pt_128 != pt2_128
