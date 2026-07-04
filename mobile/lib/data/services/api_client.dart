import 'package:dio/dio.dart';
import '../services/local_storage_service.dart';
import '../../core/constants/app_constants.dart';

/// Dio-based HTTP client for core-api.
class ApiClient {
  ApiClient._();

  static late final Dio instance;

  static void init() {
    instance = Dio(BaseOptions(
      baseUrl: AppConstants.coreApiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    instance.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = LocalStorageService.instance.authToken;
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        // Add language param
        final lang = LocalStorageService.instance.appLanguage;
        options.queryParameters['lang'] = lang;
        handler.next(options);
      },
      onError: (error, handler) {
        // RFC 7807 problem+json handling
        handler.next(error);
      },
    ));
  }
}
