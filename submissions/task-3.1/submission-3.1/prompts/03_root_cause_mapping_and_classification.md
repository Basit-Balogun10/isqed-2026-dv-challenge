- Grouped logs into UART, GPIO, Timer, SPI, AES, HMAC, and I2C clusters.
- Identified likely protocol/timing versus pure logic bugs.

## Prompt 3 - Evidence-Driven Root Cause Mapping

Prompt:
- "Map each failure to exact RTL line ranges and explain chain-of-events from logs."

Response summary:
- Pulled line-number anchors for comparator logic, interrupt mapping, edge selection, and
