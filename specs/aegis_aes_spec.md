# AEGIS_AES Specification

## AES-128 Encryption Engine

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

AEGIS_AES is a hardware AES-128 encryption and decryption engine supporting both Electronic Codebook (ECB) and Cipher Block Chaining (CBC) modes of operation. The engine implements the full AES-128 algorithm as specified in FIPS 197, performing 10 rounds of transformation on 128-bit data blocks using a 128-bit cipher key.

The module connects to the system fabric via a TileLink-UL (TL-UL) bus interface and exposes control/status registers (CSRs) for key, initialization vector (IV), plaintext, and ciphertext access. All 128-bit quantities are programmed through four consecutive 32-bit register writes. The engine supports back-to-back block operations for throughput-sensitive workloads.

A single interrupt output signals operation completion. An alert output is provided for fatal error conditions.

---

## 2. Pin Interface

| Signal        | Width  | Direction | Description                                  |
|---------------|--------|-----------|----------------------------------------------|
| `clk_i`       | 1      | Input     | System clock                                 |
| `rst_ni`      | 1      | Input     | Active-low asynchronous reset                |
| `tl_i`        | struct  | Input    | TL-UL request channel (host to device)       |
| `tl_i_ready`  | 1      | Output    | Device ready to accept TL-UL request         |
| `tl_o`        | struct  | Output   | TL-UL response channel (device to host)      |
| `tl_o_ready`  | 1      | Input     | Host ready to accept TL-UL response          |
| `intr_o`      | 1      | Output    | Interrupt output (AES operation done)        |
| `alert_o`     | 1      | Output    | Alert output                                 |

---

## 3. Functional Description

### 3.1 AES-128 Algorithm

AEGIS_AES implements the AES-128 block cipher per FIPS 197. The algorithm operates on a 4x4 byte matrix called the state, derived from the 128-bit input block. Each encryption round applies four transformations in sequence:

1. **SubBytes** -- Each byte of the state is substituted using the AES S-box, a fixed non-linear substitution table per FIPS 197.
2. **ShiftRows** -- The rows of the state matrix are cyclically shifted by row-dependent offsets.
3. **MixColumns** -- Each column of the state is treated as a polynomial over GF(2^8) and multiplied with a fixed polynomial per the AES specification.
4. **AddRoundKey** -- The state is XORed with the round key derived from the key schedule.

The initial round consists of a single AddRoundKey with the original cipher key. Rounds 1 through 9 apply all four transformations. Round 10 omits MixColumns.

Decryption applies the inverse transformations (InvSubBytes, InvShiftRows, InvMixColumns) in the order prescribed by the equivalent inverse cipher construction in FIPS 197.

### 3.2 Key Expansion

The 128-bit cipher key is expanded into 11 round keys (one for the initial AddRoundKey and one per round). Key expansion follows the FIPS 197 key schedule using the AES S-box and round constants. The engine performs key expansion internally when a start operation is triggered with a new key value. If the key has not changed since the last operation, the engine may reuse previously computed round keys.

The number of clock cycles required for key expansion is implementation-dependent. Software should poll the status register or wait for the interrupt before assuming the operation has completed.

### 3.3 Modes of Operation

**ECB (Electronic Codebook):** Each 128-bit block is encrypted or decrypted independently. No IV is used.

**CBC (Cipher Block Chaining):** For encryption, the plaintext block is XORed with the previous ciphertext block (or the IV for the first block) before encryption. For decryption, each block is decrypted and then XORed with the previous ciphertext block (or the IV for the first block) to produce the plaintext.

The IV register is updated according to the CBC specification after each block operation. Software must program the IV before the first CBC operation. For multi-block CBC sequences, the engine updates the IV internally.

### 3.4 Operation Sequence

A typical operation proceeds as follows:

1. Software writes the 128-bit key via four writes to AES_KEY_0 through AES_KEY_3.
2. If CBC mode is selected, software writes the IV via four writes to AES_IV_0 through AES_IV_3.
3. Software configures the mode (ECB/CBC) and operation (encrypt/decrypt) via AES_CTRL.
4. Software writes the 128-bit data input via four writes to AES_DATA_IN_0 through AES_DATA_IN_3.
5. Software asserts the start bit in AES_TRIGGER.
6. The engine performs key expansion (if needed), applies the 10 AES rounds, and produces the output.
7. The engine sets `output_valid` in AES_STATUS and fires the `intr_o` interrupt (if enabled).
8. Software reads the 128-bit output via four reads of AES_DATA_OUT_0 through AES_DATA_OUT_3.

### 3.5 Back-to-Back Operations

The engine supports pipelining of consecutive block operations. After a start trigger, the engine latches the input data and begins processing. The `input_ready` status bit indicates when the engine is prepared to accept new input data for the next block. Software may write new data to the AES_DATA_IN registers and assert start again once `input_ready` is asserted.

The output from the previous operation remains available in AES_DATA_OUT until overwritten by the next operation's result. Software is responsible for reading the output before it is overwritten.

### 3.6 Data and Key Clearing

Setting the `key_iv_data_in_clear` bit in AES_TRIGGER clears the key, IV, and data input registers to zero. Setting the `data_out_clear` bit clears the data output registers to zero. These operations are intended for security hygiene between distinct cryptographic contexts.

The interaction between a clear trigger and a simultaneous start trigger within the same write is not fully defined. Software should avoid asserting start and clear bits in the same trigger write.

### 3.7 FSM Description

The engine's control FSM transitions through the following states:

- **IDLE** -- Awaiting a start trigger. All status bits reflect quiescent state.
- **KEY_EXPAND** -- Computing round keys from the cipher key. Duration is implementation-dependent.
- **INIT_CBC** -- (CBC mode only) Preparing the IV for the first round XOR.
- **ROUND** -- Executing AES rounds 1 through 10 sequentially. Each round completes in one clock cycle.
- **DONE** -- Output is available. The engine remains in DONE until a new operation is started or until it returns to IDLE.

The transition from DONE back to IDLE or to a new operation depends on whether back-to-back mode is active and whether new input has been provided.

---

## 4. CSR Register Map

All registers are 32 bits wide. Byte address offsets are given relative to the module base address. The 128-bit key, IV, data input, and data output are each spread across four consecutive 32-bit registers with the least-significant word at the lowest address.

| Offset | Name            | Access | Description                                        |
|--------|-----------------|--------|----------------------------------------------------|
| 0x00   | AES_KEY_0       | WO     | Key bits [31:0]                                    |
| 0x04   | AES_KEY_1       | WO     | Key bits [63:32]                                   |
| 0x08   | AES_KEY_2       | WO     | Key bits [95:64]                                   |
| 0x0C   | AES_KEY_3       | WO     | Key bits [127:96]                                  |
| 0x10   | AES_IV_0        | RW     | IV bits [31:0]                                     |
| 0x14   | AES_IV_1        | RW     | IV bits [63:32]                                    |
| 0x18   | AES_IV_2        | RW     | IV bits [95:64]                                    |
| 0x1C   | AES_IV_3        | RW     | IV bits [127:96]                                   |
| 0x20   | AES_DATA_IN_0   | WO     | Data input bits [31:0]                             |
| 0x24   | AES_DATA_IN_1   | WO     | Data input bits [63:32]                            |
| 0x28   | AES_DATA_IN_2   | WO     | Data input bits [95:64]                            |
| 0x2C   | AES_DATA_IN_3   | WO     | Data input bits [127:96]                           |
| 0x30   | AES_DATA_OUT_0  | RO     | Data output bits [31:0]                            |
| 0x34   | AES_DATA_OUT_1  | RO     | Data output bits [63:32]                           |
| 0x38   | AES_DATA_OUT_2  | RO     | Data output bits [95:64]                           |
| 0x3C   | AES_DATA_OUT_3  | RO     | Data output bits [127:96]                          |
| 0x40   | AES_CTRL        | RW     | Control register                                   |
| 0x44   | AES_TRIGGER     | W1S    | Trigger register                                   |
| 0x48   | AES_STATUS      | RO     | Status register                                    |
| 0x4C   | INTR_STATE      | W1C    | Interrupt status                                   |
| 0x50   | INTR_ENABLE     | RW     | Interrupt enable                                   |
| 0x54   | INTR_TEST       | RW     | Interrupt test                                     |

### 4.1 AES_KEY_0 through AES_KEY_3 (0x00 -- 0x0C)

Write-only registers that hold the 128-bit cipher key. Reading these registers returns zero. The key is latched internally when a start trigger is asserted. Writing fewer than four key words before triggering an operation may result in unpredictable behavior; the engine does not track partial key writes.

### 4.2 AES_IV_0 through AES_IV_3 (0x10 -- 0x1C)

Read-write registers that hold the 128-bit initialization vector for CBC mode. In ECB mode, the IV registers are ignored. In CBC mode, the engine reads the IV at the start of an operation and updates it upon completion.

Software may read back the IV registers at any time to observe the current IV value, including after an automatic update from a CBC operation.

### 4.3 AES_DATA_IN_0 through AES_DATA_IN_3 (0x20 -- 0x2C)

Write-only registers for the 128-bit input data block. Reading these registers returns zero. The data is latched when the start trigger is asserted.

### 4.4 AES_DATA_OUT_0 through AES_DATA_OUT_3 (0x30 -- 0x3C)

Read-only registers containing the 128-bit output of the most recently completed operation. The contents of these registers before any operation has completed are undefined.

### 4.5 AES_CTRL (0x40)

| Bits  | Field      | Reset | Description                                         |
|-------|------------|-------|-----------------------------------------------------|
| [0]   | mode       | 0     | 0 = ECB, 1 = CBC                                   |
| [1]   | operation  | 0     | 0 = encrypt, 1 = decrypt                           |
| [31:2]| reserved   | 0     | Reserved. Writes ignored, reads as zero.            |

Changes to AES_CTRL while the engine is processing an operation take effect on the next operation. The engine does not abort an in-progress operation due to a control register change.

### 4.6 AES_TRIGGER (0x44)

| Bits  | Field                | Reset | Description                                   |
|-------|----------------------|-------|-----------------------------------------------|
| [0]   | start                | 0     | Write 1 to begin an AES operation             |
| [1]   | key_iv_data_in_clear | 0     | Write 1 to clear key, IV, and data-in regs    |
| [2]   | data_out_clear       | 0     | Write 1 to clear data-out registers           |
| [31:3]| reserved             | 0     | Reserved                                      |

This register uses write-1-to-set (W1S) semantics. The trigger bits are self-clearing; they are automatically deasserted by hardware after the corresponding action is initiated. Reads from this register always return zero.

Writing start while the engine is not idle has no effect; the trigger is ignored and the in-progress operation continues undisturbed.

### 4.7 AES_STATUS (0x48)

| Bits  | Field         | Reset | Description                                      |
|-------|---------------|-------|--------------------------------------------------|
| [0]   | idle          | 1     | Engine is idle and ready for configuration       |
| [1]   | output_valid  | 0     | Output data registers contain valid result       |
| [2]   | input_ready   | 1     | Engine can accept new input data                 |
| [3]   | stall         | 0     | Engine has stalled (reserved for future use)     |
| [31:4]| reserved      | 0     | Reserved                                         |

The `output_valid` bit is set when an operation completes and remains set until a new operation is started or the output is explicitly cleared.

The `input_ready` bit indicates that the engine can accept new data for a subsequent operation. This bit may be asserted before the current operation completes to support back-to-back scheduling. The exact timing of `input_ready` reassertion relative to the processing pipeline is implementation-dependent.

### 4.8 INTR_STATE (0x4C)

| Bits  | Field     | Reset | Description                                        |
|-------|-----------|-------|----------------------------------------------------|
| [0]   | aes_done  | 0     | Set when an AES operation completes                |
| [31:1]| reserved  | 0     | Reserved                                           |

Write-1-to-clear semantics. Writing a 1 to bit 0 clears the `aes_done` interrupt status. The `intr_o` output reflects `INTR_STATE[0] & INTR_ENABLE[0]`.

### 4.9 INTR_ENABLE (0x50)

| Bits  | Field     | Reset | Description                                        |
|-------|-----------|-------|----------------------------------------------------|
| [0]   | aes_done  | 0     | Enable interrupt for AES operation completion      |
| [31:1]| reserved  | 0     | Reserved                                           |

### 4.10 INTR_TEST (0x54)

| Bits  | Field     | Reset | Description                                        |
|-------|-----------|-------|----------------------------------------------------|
| [0]   | aes_done  | 0     | Write 1 to inject an aes_done interrupt event      |
| [31:1]| reserved  | 0     | Reserved                                           |

Writing 1 to bit 0 causes INTR_STATE[0] to be set, simulating an operation completion for interrupt handler testing. The injected interrupt follows normal W1C clearing behavior.

---

## 5. Timing Considerations

- The TL-UL interface responds in a single cycle for all CSR read and write accesses.
- Key expansion begins on the clock cycle following a start trigger assertion. The duration of key expansion is not specified; software must not assume a fixed latency.
- Each AES round executes in one clock cycle. There are 10 rounds for AES-128.
- The total operation latency from start trigger to output_valid assertion includes key expansion time plus 10 round cycles, plus any initialization overhead for CBC mode.
- The interrupt output (`intr_o`) updates combinationally from INTR_STATE and INTR_ENABLE.
- The `idle` status bit deasserts on the cycle following a valid start trigger and reasserts when the engine returns to the IDLE state.

---

## 6. Reset Behavior

On assertion of `rst_ni` (active-low), all internal registers and state are cleared to zero, with the following exceptions:

- AES_STATUS resets to `idle = 1, output_valid = 0, input_ready = 1, stall = 0`.
- The FSM resets to the IDLE state.
- AES_CTRL resets to `mode = ECB, operation = encrypt`.

All data path registers (key, IV, data in, data out) reset to zero.

---

## 7. Alert Behavior

The `alert_o` signal is reserved for fatal error conditions. Under normal operation, `alert_o` remains deasserted. The specific conditions under which an alert may fire are related to internal consistency checks and are not enumerated in this specification.

---

## 8. Known-Answer Test Guidance

Verification of cryptographic correctness should employ known-answer tests (KATs) derived from FIPS 197 and NIST SP 800-38A. The following test classes are recommended:

- **ECB encrypt/decrypt** with the FIPS 197 Appendix B test vector (key = `2b7e151628aed2a6abf7158809cf4f3c`, plaintext = `3243f6a8885a308d313198a2e0370734`)
- **CBC encrypt** with NIST SP 800-38A test vectors
- **CBC decrypt** verifying that decrypt(encrypt(P)) = P for all test vectors
- **Round-trip** verification for arbitrary data patterns

Specific S-box entries, round constant values, and MixColumns coefficients are as defined in FIPS 197 and are not reproduced here.
