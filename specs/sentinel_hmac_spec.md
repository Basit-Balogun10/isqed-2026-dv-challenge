# SENTINEL_HMAC -- HMAC-SHA256 Accelerator

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

SENTINEL_HMAC is a hardware accelerator implementing keyed-hash message authentication (HMAC) based on SHA-256, as specified in RFC 2104, as well as a raw SHA-256 hashing mode per FIPS 180-4. The module accepts message data through a 32-entry write FIFO and produces a 256-bit digest, accessible through memory-mapped control/status registers over a TileLink-UL (TL-UL) bus interface.

HMAC mode computes `HMAC(K, m) = SHA-256((K XOR opad) || SHA-256((K XOR ipad) || m))` using the standard inner/outer padding constants. SHA-256-only mode bypasses HMAC key processing and computes the bare hash of the supplied message. Both modes support multi-block streaming: software writes message data in arbitrarily-sized chunks and issues control commands to advance the hash computation.

The SHA-256 core performs one compression round per clock cycle, requiring 64 cycles per 512-bit message block. Message schedule expansion is performed on-the-fly during compression. Padding (appending the terminating 1-bit, zero fill, and 64-bit message length) is handled automatically when software signals the end of the message.

## 2. Block-Level Architecture

```
                    TL-UL Bus
                       |
                +------+------+
                |  CSR Block  |
                +--+--+--+--+-+
                   |  |  |  |
          +--------+  |  |  +--------+
          |           |  |           |
    +-----+-----+    |  |    +------+------+
    | KEY Regs   |    |  |    | DIGEST Regs |
    | (256-bit)  |    |  |    | (256-bit)   |
    +-----+------+    |  |    +------+------+
          |           |  |           |
    +-----+------+    |  |           |
    | HMAC       |    |  |           |
    | Key Expand |    |  |           |
    +-----+------+    |  |           |
          |      +----+--+----+      |
          +----->| MSG FIFO   |      |
                 | 32x32-bit  |      |
                 +-----+------+      |
                       |             |
                 +-----+------+      |
                 | 512-bit    |      |
                 | Block Buf  |      |
                 +-----+------+      |
                       |             |
                 +-----+------+      |
                 | SHA-256    |      |
                 | Engine     +------+
                 | (64 rounds)|
                 +------------+
```

In HMAC mode, the key expansion block first XORs the 256-bit key (zero-padded to 512 bits) with the inner pad value and feeds the resulting 512-bit block directly into the SHA-256 engine before any message data is processed. After the message is fully hashed, the intermediate digest is then used as the message input for a second SHA-256 pass with the outer-pad-XORed key block prepended.

## 3. Signal Interface

| Signal       | Direction | Width   | Description                                |
|--------------|-----------|---------|--------------------------------------------|
| `clk_i`      | Input     | 1       | System clock                               |
| `rst_ni`     | Input     | 1       | Active-low asynchronous reset              |
| `tl_i`       | Input     | packed  | TL-UL A-channel request (tl_a_pkt_t)      |
| `tl_i_ready` | Output    | 1       | Backpressure for A-channel                 |
| `tl_o`       | Output    | packed  | TL-UL D-channel response (tl_d_pkt_t)     |
| `tl_o_ready` | Input     | 1       | Downstream ready for D-channel             |
| `intr_o`     | Output    | 3       | Interrupt vector (active-high)             |
| `alert_o`    | Output    | 1       | Fatal alert (integrity error, etc.)        |

The TL-UL interface follows the simplified protocol defined in `dv_common_pkg`. A-channel transactions with `a_opcode` of `PutFullData` (0) perform writes; transactions with `a_opcode` of `Get` (4) perform reads. The device responds in the same cycle the request is accepted. Requests to unmapped addresses receive an error response.

## 4. Register Map

Base offset: 0x00. All registers are 32 bits wide. Undefined bit fields read as zero; writes to undefined fields are ignored.

### 4.1 CFG (0x00) -- Configuration Register [RW]

| Bits   | Field        | Reset | Description                                           |
|--------|--------------|-------|-------------------------------------------------------|
| 0      | hmac_en      | 0     | Enable HMAC mode (key processing + double SHA pass)   |
| 1      | sha_en       | 0     | Enable SHA-256 engine                                 |
| 2      | endian_swap  | 0     | Swap byte ordering of incoming message words          |
| 3      | digest_swap  | 0     | Swap byte ordering of digest output words             |
| 31:4   | --           | --    | Reserved                                              |

Setting `hmac_en` without `sha_en` is not a valid configuration. When `hmac_en` is 0 and `sha_en` is 1, the module performs bare SHA-256 without HMAC key processing. The `endian_swap` and `digest_swap` fields control byte-order transformations applied to data as it enters and exits the hash engine. The exact transformation behavior follows common practice for big-endian SHA-256 operating over a little-endian bus.

### 4.2 CMD (0x04) -- Command Register [W1S]

| Bits   | Field        | Description                                            |
|--------|--------------|--------------------------------------------------------|
| 0      | hash_start   | Begin a new hash operation; resets internal state      |
| 1      | hash_process | Process the current FIFO contents as a message block   |
| 2      | hash_stop    | Finalize: apply padding and compute the final digest   |
| 31:3   | --           | Reserved                                               |

Commands are edge-triggered (write-1-to-set, self-clearing). `hash_start` initializes the SHA-256 state to the standard initial hash values (or processes the ipad key block in HMAC mode) and resets the message length counter. `hash_process` triggers compression of accumulated data in the FIFO without finalization. `hash_stop` appends SHA-256 padding to the remaining message data and completes the hash. In HMAC mode, `hash_stop` additionally triggers the outer hash pass automatically.

Software must issue `hash_start` before writing any message data. The sequencing requirements for `hash_process` versus `hash_stop` when the FIFO contains a partial block are left to standard SHA-256 padding behavior.

### 4.3 STATUS (0x08) -- Status Register [RO]

| Bits   | Field        | Description                                            |
|--------|--------------|--------------------------------------------------------|
| 0      | fifo_full    | Message FIFO is at capacity                            |
| 1      | fifo_empty   | Message FIFO contains no entries                       |
| 7:2    | fifo_depth   | Number of 32-bit entries currently in the FIFO         |
| 8      | sha_idle     | SHA-256 engine is idle and ready for a new operation   |
| 31:9   | --           | Reserved                                               |

### 4.4 WIPE_SECRET (0x0C) -- Secret Wipe Register [W1S]

| Bits   | Field        | Description                                            |
|--------|--------------|--------------------------------------------------------|
| 0      | wipe         | Write 1 to clear key registers and internal state      |
| 31:1   | --           | Reserved                                               |

Writing 1 to the wipe bit clears the HMAC key registers to zero and resets secret-related internal state. This is intended for security zeroization after an HMAC operation completes. The scope of what internal state is cleared (e.g., whether the message schedule registers, intermediate hash state, or FIFO contents are also wiped) follows the design's zeroization policy.

### 4.5 KEY_0 through KEY_7 (0x10 -- 0x2C) -- HMAC Key Registers [WO]

Eight 32-bit registers holding the 256-bit HMAC secret key. KEY_0 holds the most significant 32 bits of the key. These registers are write-only; reads return zero. The key must be written before issuing `hash_start` in HMAC mode. Key handling for keys shorter than 256 bits follows RFC 2104.

### 4.6 DIGEST_0 through DIGEST_7 (0x30 -- 0x4C) -- Digest Output Registers [RO]

Eight 32-bit registers containing the computed 256-bit hash digest. DIGEST_0 holds the first (most significant) 32-bit word of the digest. These registers are valid after the `hmac_done` interrupt fires and remain stable until the next hash operation begins.

### 4.7 MSG_LENGTH_LOWER (0x50) -- Message Length Low [RO]

Lower 32 bits of the total message length in bits. This counter accumulates as message data is written to the FIFO and is used internally for SHA-256 padding.

### 4.8 MSG_LENGTH_UPPER (0x54) -- Message Length High [RO]

Upper 32 bits of the total message length in bits, supporting messages up to 2^64 - 1 bits.

### 4.9 INTR_STATE (0x58) -- Interrupt State Register [W1C]

| Bit | Field        | Description                                             |
|-----|--------------|---------------------------------------------------------|
| 0   | hmac_done    | Hash/HMAC computation completed; digest is ready        |
| 1   | fifo_empty   | Message FIFO has become empty                           |
| 2   | hmac_err     | Error condition detected                                |

Bits are set by hardware and cleared by writing 1 to the corresponding position.

### 4.10 INTR_ENABLE (0x5C) -- Interrupt Enable Register [RW]

Each bit enables the corresponding INTR_STATE bit to propagate to the `intr_o` output. When a bit is 0, the corresponding interrupt is masked but INTR_STATE still reflects the underlying condition.

### 4.11 INTR_TEST (0x60) -- Interrupt Test Register [RW]

Writing 1 to any bit forces the corresponding INTR_STATE bit to set, regardless of hardware state. Used for interrupt controller integration testing. Reads return 0.

### 4.12 MSG_FIFO (0x64) -- Message FIFO Write Port [WO]

Write-only port for message data. Each write pushes one 32-bit word into the message FIFO. The `a_mask` field of the TL-UL transaction indicates which byte lanes are valid, supporting sub-word writes for message lengths that are not multiples of 4 bytes.

Software should monitor STATUS.fifo_full before writing. The behavior when writing to MSG_FIFO while the FIFO is full follows standard peripheral practice.

## 5. SHA-256 Engine

The SHA-256 engine implements the compression function as defined in FIPS 180-4. The engine accepts 512-bit message blocks and produces a 256-bit intermediate hash value that is chained across successive blocks.

### 5.1 Initial Hash Values

The eight initial hash values (H0 through H7) are loaded at the start of each new hash computation, per FIPS 180-4 Section 5.3.3.

### 5.2 Message Schedule

For each 512-bit block, the sixteen 32-bit words from the block form W[0] through W[15]. The remaining entries W[16] through W[63] are computed using the recurrence relation specified in FIPS 180-4, involving the lower-case sigma functions. The schedule is computed on-the-fly during compression rounds.

### 5.3 Compression

The compression function processes 64 rounds, each updating eight working variables (a through h) using the round constant K[t], the schedule word W[t], and the Sigma, Ch, and Maj functions. After all 64 rounds, the working variables are added to the current intermediate hash value to produce the updated hash state.

### 5.4 Padding

When `hash_stop` is issued, the engine automatically applies SHA-256 padding to the final message data: a 1-bit is appended after the last message bit, followed by enough zero bits to bring the padded block to 448 bits modulo 512, followed by the 64-bit big-endian representation of the total message length in bits. If the remaining data plus padding does not fit in a single 512-bit block, two blocks are generated.

## 6. HMAC Operation

### 6.1 Key Processing

In HMAC mode, the 256-bit key is zero-padded to 512 bits (the SHA-256 block size). The padded key is XORed with the inner pad constant (each byte 0x36) to produce the ipad block, and XORed with the outer pad constant (each byte 0x5c) to produce the opad block. Key preparation for keys of different lengths follows RFC 2104.

### 6.2 Inner Hash

Upon `hash_start` with `hmac_en` asserted, the engine first compresses the ipad block as the first message block, then accepts message data from the FIFO for subsequent blocks. When `hash_stop` is issued, padding is applied and the inner hash is computed.

### 6.3 Outer Hash

After the inner hash completes, the engine automatically initiates the outer hash: it reinitializes the SHA-256 state, compresses the opad block, then feeds the 256-bit inner digest (zero-padded to a full block) through the compression function with standard padding. The final digest placed in the DIGEST registers is the HMAC output.

## 7. Streaming Interface

The streaming interface allows software to hash messages of arbitrary length across multiple FIFO fills.

1. Write `hash_start` to CMD to initialize a new operation.
2. Write message data to MSG_FIFO. When the internal 512-bit block buffer is full (16 words accumulated), the SHA-256 engine automatically begins compression.
3. If the FIFO fills before all message data is written, software may wait for the engine to drain words and then continue writing.
4. To process accumulated data without finalizing, software may issue `hash_process`.
5. After all message data has been written, write `hash_stop` to CMD. The engine pads the remaining data and computes the final digest.
6. Wait for the `hmac_done` interrupt, then read DIGEST_0 through DIGEST_7.

The behavior of issuing `hash_process` or `hash_stop` while the engine is actively compressing a block, or issuing `hash_stop` when the FIFO is empty and no partial block exists, is governed by the engine's internal state machine.

## 8. Interrupts

SENTINEL_HMAC generates 3 interrupt sources output as a packed 3-bit vector on `intr_o[2:0]`.

| Bit | Source       | Condition                                               |
|-----|--------------|---------------------------------------------------------|
| 0   | hmac_done    | Hash computation finished; digest registers are valid   |
| 1   | fifo_empty   | Message FIFO has transitioned to empty                  |
| 2   | hmac_err     | Error detected (invalid command sequence, etc.)         |

The output vector is computed as: `intr_o = intr_state & intr_enable`.

Interrupt sources are level-based internally. INTR_STATE latches assertions. Software clears an interrupt by writing 1 to the corresponding INTR_STATE bit.

## 9. Error Conditions

The `hmac_err` interrupt is raised when the engine detects an invalid operational condition. Examples include issuing hash commands when the engine is not idle, or attempting HMAC operations without proper key configuration. The full set of error-triggering conditions is not exhaustively enumerated; teams should characterize error behavior empirically.

## 10. Alert Output

The `alert_o` signal is reserved for fatal hardware errors such as internal state corruption. Under normal operation, `alert_o` remains deasserted.

## 11. Reset Behavior

On assertion of `rst_ni` (active-low), all registers return to their reset values, the message FIFO is flushed, the SHA-256 engine returns to idle, and all internal state (including key registers and intermediate hash values) is cleared. The reset is asynchronous and takes effect regardless of clock state.
