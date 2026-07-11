import 'package:dio/dio.dart';
import '../services/api_client.dart';
import '../models/auth_model.dart';

/// Repository for email/password authentication: signup and login.
///
/// Both calls return a [AuthResult] carrying the backend JWT. The [ApiClient]
/// interceptor automatically attaches that token to every subsequent request.
class AuthRepository {
  final ApiClient _client;

  AuthRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Create a brand-new account. The new user starts with zero progress.
  Future<AuthResult> signup({
    required String email,
    required String password,
    String? displayName,
  }) async {
    try {
      final response = await _client.post(
        '/auth/signup',
        data: {
          'email': email,
          'password': password,
          if (displayName != null && displayName.isNotEmpty)
            'display_name': displayName,
        },
      );
      return AuthResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Authenticate with email + password and receive a JWT.
  Future<AuthResult> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _client.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );
      return AuthResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
