# Generic Peripheral Controller Specification

## Version

Version: 1.0

## Overview

The Generic Peripheral Controller mediates host requests to a peripheral data path.
The block supports request acceptance, queued processing, response generation,
status reporting, and interrupt signaling for completion and error conditions.

## Functional Requirements

### Core operation

- The controller shall accept valid requests when enabled.
- Each accepted request shall eventually produce one response.
- Responses shall preserve request ordering.

### Configuration model

- A control register shall enable/disable processing.
- A mode field selects normal, diagnostic, or low-power operation.
- Illegal mode encodings shall raise an error status.

### Queue behavior

- Input requests are buffered in a finite queue.
- Queue full condition shall reject new requests and set overflow status.
- Queue empty condition shall indicate idle state.

### Event and interrupt behavior

- Completion interrupt shall assert when a request completes and interrupt enable
  is set.
- Error interrupt shall assert when any enabled error status bit is set.
- Writing clear bits shall deassert corresponding interrupt sources.

### Error behavior

- Protocol format violations shall set a protocol_error status.
- Queue overflow shall set an overflow_error status.
- Errors shall not silently corrupt already accepted requests.

### Reset behavior

- Reset restores all control/status defaults.
- Queue returns to empty.
- Outputs return to safe idle state.
