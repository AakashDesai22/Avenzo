import 'dart:math';

/// Lightweight RFC 4122 v4 UUID generator for client-side idempotency keys.
class UuidGenerator {
  UuidGenerator._();

  static final Random _random = Random.secure();

  /// Generates a random v4 UUID string (e.g. `f47ac10b-58cc-4372-a567-0e02b2c3d479`)
  static String generateV4() {
    final bytes = List<int>.generate(16, (_) => _random.nextInt(256));

    // Set version (4) and variant (RFC 4122)
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    String hex(int byte) => byte.toRadixString(16).padLeft(2, '0');

    final b = bytes.map(hex).toList();

    return '${b[0]}${b[1]}${b[2]}${b[3]}-'
        '${b[4]}${b[5]}-'
        '${b[6]}${b[7]}-'
        '${b[8]}${b[9]}-'
        '${b[10]}${b[11]}${b[12]}${b[13]}${b[14]}${b[15]}';
  }
}
