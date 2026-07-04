import 'dart:math';

/// Utility for generating idempotency keys for API requests.
/// Ensures that retried requests don't create duplicate resources.
class IdempotencyKey {
  IdempotencyKey._();

  /// Generates a random idempotency key (UUID v4 format).
  static String generate() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));

    // Set version (4) and variant bits
    bytes[6] = (bytes[6] & 0x0F) | 0x40;
    bytes[8] = (bytes[8] & 0x3F) | 0x80;

    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-'
        '${hex.substring(12, 16)}-${hex.substring(16, 20)}-'
        '${hex.substring(20)}';
  }

  /// Generates a deterministic idempotency key from a prefix and timestamp.
  /// Useful for operations that should be idempotent within a time window.
  static String forAction(String action, {DateTime? at}) {
    final timestamp = (at ?? DateTime.now()).millisecondsSinceEpoch;
    return 'qari-$action-$timestamp';
  }
}
