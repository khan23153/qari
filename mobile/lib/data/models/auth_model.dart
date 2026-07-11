/// Result of a successful signup / login.
class AuthResult {
  final String accessToken;
  final String tokenType;
  final int expiresIn;
  final String userId;
  final bool isOnboarded;

  const AuthResult({
    required this.accessToken,
    required this.tokenType,
    required this.expiresIn,
    required this.userId,
    required this.isOnboarded,
  });

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
      accessToken: json['access_token'] as String,
      tokenType: (json['token_type'] as String?) ?? 'Bearer',
      expiresIn: (json['expires_in'] as int?) ?? 0,
      userId: json['user_id'].toString(),
      isOnboarded: (json['is_onboarded'] as bool?) ?? false,
    );
  }
}
