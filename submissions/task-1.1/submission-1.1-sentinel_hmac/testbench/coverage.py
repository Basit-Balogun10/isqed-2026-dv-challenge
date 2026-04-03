"""
HMAC Coverage Model for sentinel_hmac DUT

Tracks functional coverage for HMAC-SHA256 accelerator including:
  - Key length configurations
  - Message length variations
  - Block processing counts
  - CSR access patterns
"""

class HmacCoverageModel:
    """HMAC functional coverage collector."""

    def __init__(self, log=None):
        self.log = log
        self.key_lengths_covered = set()
        self.message_lengths_covered = set()
        self.blocks_processed = 0
        self.csr_accesses = {'reads': 0, 'writes': 0}
        self.operations_completed = 0

    def record_key_length(self, length):
        self.key_lengths_covered.add(length)
        if self.log:
            self.log.debug(f"[Coverage] HMAC key length: {length}")

    def record_message_length(self, length):
        if length < 1000:
            bucket = f"<1KB"
        elif length < 1000000:
            bucket = f"<1MB"
        else:
            bucket = f">1MB"
        self.message_lengths_covered.add(bucket)

    def record_block_processed(self):
        self.blocks_processed += 1

    def record_operation_completed(self):
        self.operations_completed += 1

    def record_csr_access(self, access_type):
        if access_type in self.csr_accesses:
            self.csr_accesses[access_type] += 1

    def report(self):
        print("\n" + "=" * 60)
        print("HMAC COVERAGE REPORT")
        print("=" * 60)
        print(f"Key lengths covered: {sorted(self.key_lengths_covered)}")
        print(f"Message size ranges: {self.message_lengths_covered}")
        print(f"Blocks processed: {self.blocks_processed}")
        print(f"Operations completed: {self.operations_completed}")
        print(f"CSR operations: {self.csr_accesses}")
        print("=" * 60 + "\n")
