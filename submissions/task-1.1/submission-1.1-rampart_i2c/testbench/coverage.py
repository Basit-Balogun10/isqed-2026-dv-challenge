"""
I2C Coverage Model for rampart_i2c DUT

Tracks functional coverage for I2C host/target controller including:
  - Speed modes (100kHz, 400kHz, etc.)
  - Transaction types (read, write, repeated start)
  - Error conditions
  - Multi-master arbitration
  - Clock stretching scenarios
"""

class I2cCoverageModel:
    """I2C functional coverage collector."""

    def __init__(self, log=None):
        self.log = log
        self.speed_modes_covered = set()  # {'100kHz', '400kHz', '1MHz'}
        self.transaction_types = set()  # {'read', 'write', 'repeated_start'}
        self.error_types_seen = set()
        self.arbitration_events = 0
        self.clock_stretches = 0
        self.csr_accesses = {'reads': 0, 'writes': 0}
        self.transactions_completed = 0

    def record_speed_mode(self, mode):
        self.speed_modes_covered.add(mode)
        if self.log:
            self.log.debug(f"[Coverage] I2C speed: {mode}")

    def record_transaction(self, tx_type):
        self.transaction_types.add(tx_type)

    def record_error(self, error):
        self.error_types_seen.add(error)

    def record_arbitration_event(self):
        self.arbitration_events += 1

    def record_clock_stretch(self):
        self.clock_stretches += 1

    def record_transaction_done(self):
        self.transactions_completed += 1

    def record_csr_access(self, access_type):
        if access_type in self.csr_accesses:
            self.csr_accesses[access_type] += 1

    def report(self):
        print("\n" + "=" * 60)
        print("I2C COVERAGE REPORT")
        print("=" * 60)
        print(f"Speed modes covered: {self.speed_modes_covered}")
        print(f"Transaction types: {self.transaction_types}")
        print(f"Errors observed: {self.error_types_seen}")
        print(f"Arbitration events: {self.arbitration_events}")
        print(f"Clock stretches: {self.clock_stretches}")
        print(f"Transactions completed: {self.transactions_completed}")
        print(f"CSR operations: {self.csr_accesses}")
        print("=" * 60 + "\n")
