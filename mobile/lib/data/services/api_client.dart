import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../../core/constants/app_constants.dart';
import 'local_storage_service.dart';

/// Dio-based HTTP client with auth interceptor, language param injection,
/// and centralized error handling.
class ApiClient {
  late final Dio _dio;
  final LocalStorageService _storage = LocalStorageService();

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: Duration(seconds: AppConstants.apiTimeoutSeconds),
      receiveTimeout: Duration(seconds: AppConstants.apiTimeoutSeconds),
      sendTimeout: Duration(seconds: AppConstants.apiTimeoutSeconds),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _setupInterceptors();
  }

  Dio get dio => _dio;

  void _setupInterceptors() {
    // Auth + Language interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Inject auth token
        final token = await _storage.getAuthToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }

        // Inject language preference
        final lang = await _storage.getSelectedLanguage();
        if (lang != null) {
          options.headers['Accept-Language'] = lang;
          options.queryParameters['lang'] = lang;
        }

        // Inject idempotency key for POST/PUT/DELETE
        if (options.method == 'POST' || options.method == 'PUT' || options.method == 'PATCH') {
          options.headers['Idempotency-Key'] ??=
              DateTime.now().millisecondsSinceEpoch.toString();
        }

        handler.next(options);
      },
      onError: (error, handler) {
        // Centralized error logging
        if (kDebugMode) {
          debugPrint('API Error: ${error.response?.statusCode} '
              '${error.requestOptions.path} - ${error.message}');
        }
        handler.next(error);
      },
    ));

    // Logging interceptor (debug only)
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        requestHeader: false,
        error: true,
        logPrint: (obj) => debugPrint('[DIO] $obj'),
      ));
    }
  }

  // ─── HTTP Methods ────────────────────────────────────────────────────────

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  // ─── File Upload ─────────────────────────────────────────────────────────
  Future<Response<T>> uploadFile<T>(
    String path, {
    required String filePath,
    String fieldName = 'file',
    Map<String, dynamic>? extraFields,
    ProgressCallback? onProgress,
  }) async {
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(filePath),
      ...?extraFields,
    });

    return _dio.post<T>(
      path,
      data: formData,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
      ),
      onSendProgress: onProgress,
    );
  }
}

/// Custom API exception for structured error handling.
class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final String? errorCode;
  final Map<String, dynamic>? details;

  const ApiException({
    this.statusCode,
    required this.message,
    this.errorCode,
    this.details,
  });

  factory ApiException.fromDioError(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return const ApiException(
        statusCode: 408,
        message: 'Connection timed out. Please check your internet connection.',
        errorCode: 'TIMEOUT',
      );
    }

    if (error.type == DioExceptionType.connectionError) {
      return const ApiException(
        statusCode: 0,
        message: 'No internet connection. Please check your network.',
        errorCode: 'NO_CONNECTION',
      );
    }

    final response = error.response;
    if (response != null) {
      final data = response.data as Map<String, dynamic>?;
      return ApiException(
        statusCode: response.statusCode,
        message: data?['message'] ?? 'An error occurred. Please try again.',
        errorCode: data?['error_code'] as String?,
        details: data,
      );
    }

    return ApiException(
      statusCode: error.type == DioExceptionType.unknown ? 500 : null,
      message: error.message ?? 'An unexpected error occurred.',
    );
  }

  bool get isNetworkError =>
      errorCode == 'TIMEOUT' || errorCode == 'NO_CONNECTION';

  bool get isAuthError => statusCode == 401 || statusCode == 403;

  bool get isNotFound => statusCode == 404;

  bool get isServerError => statusCode != null && statusCode! >= 500;

  @override
  String toString() => 'ApiException($statusCode): $message';
}
