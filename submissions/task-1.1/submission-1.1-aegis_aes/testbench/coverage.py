"""
AES Coverage Model for aegis_aes DUT

Tracks functional coverage for AES encryption/decryption engine including:
  - Mode configurations (ECB, CBC)
  - Key sizes
  - Data patterns and edge cases
  - CSR access patterns
"""

class AesCoverageModel:
    """AES functional coverage collector."""

    def __init__(self, log=None):
        self.log = log
        self.modes_covered = set()  # {'ECB', 'CBC'}
        self.key_sizes_covered = set()  # {128, 192, 256} bits
        self.operations_covered = set()  # {'encrypt', 'decrypt'}
        self.csr_accesses = {'reads': 0, 'writes': 0}
        self.block_count = 0
        self.errors_seen = set()

    def record_mode(self, mode):
        self.modes_covered.add(mode)
        if self.log:
            self.log.debug(f"[Coverage] AES mode: {mode}")

    def record_key_size(self, size):
        self.key_sizes_covered.add(size)

    def record_operation(self, op):
        self.operations_covered.add(op)

    def record_block(self):
        self.block_count += 1

    def record_csr_access(self, access_type):
        if access_type in self.csr_accesses:
            self.csr_accesses[access_type] += 1

    def report(self):
        print("\n" + "=" * 60)
        print("AES COVERAGE REPORT")
        print("=" * 60)
        print(f"Modes covered: {self.modes_covered}")
        print(f"Key sizes covered: {sorted(self.key_sizes_covered)} bits")
        print(f"Operations covered: {self.operations_covered}")
        print(f"Blocks processed: {self.block_count}")
        print(f"CSR operations: {self.csr_accesses}")
        print("=" * 60 + "\n")
