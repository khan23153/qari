import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:open_filex/open_filex.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';

import '../../data/services/api_client.dart';

/// Latest app release metadata returned by the backend ``/v1/app/version``
/// endpoint.  Drives over-the-air (OTA) update prompts.
class AppRelease {
  const AppRelease({
    required this.version,
    required this.versionCode,
    required this.minVersion,
    required this.minVersionCode,
    required this.apkUrl,
    required this.forceUpdate,
    this.notes = const <String, String>{},
    this.dataVersion = 0,
  });

  factory AppRelease.fromJson(Map<String, dynamic> j) {
    final notes = <String, String>{};
    for (final key in const ['notes_en', 'notes_ur', 'notes_ar']) {
      final value = j[key];
      if (value is String && value.isNotEmpty) {
        notes[key.split('_').last] = value;
      }
    }
    return AppRelease(
      version: j['version']?.toString() ?? '',
      versionCode: _toInt(j['version_code']),
      minVersion: j['min_version']?.toString() ?? '',
      minVersionCode: _toInt(j['min_version_code']),
      apkUrl: j['apk_url']?.toString() ?? '',
      forceUpdate: j['force_update'] == true,
      notes: notes,
      dataVersion: _toInt(j['data_version']),
    );
  }

  final String version;
  final int versionCode;
  final String minVersion;
  final int minVersionCode;
  final String apkUrl;
  final bool forceUpdate;
  final Map<String, String> notes;
  final int dataVersion;

  static int _toInt(dynamic v) {
    if (v is int) return v;
    if (v is String) return int.tryParse(v) ?? 0;
    return 0;
  }
}

/// Result of comparing the installed app against the backend release info.
class UpdateDecision {
  const UpdateDecision({required this.release, required this.mandatory});

  final AppRelease release;
  final bool mandatory;
}

/// Checks the backend for a newer app build and downloads/installs it.
class AppUpdateService {
  AppUpdateService(this._api);

  final ApiClient _api;

  /// Returns an [UpdateDecision] when a newer release is available, else null.
  /// Fails soft (returns null) on any network/parse error so the app
  /// keeps working even if the release endpoint is unavailable.
  Future<UpdateDecision?> checkForUpdate() async {
    try {
      final resp = await _api.get<dynamic>('/app/version');
      if (resp.statusCode != 200 || resp.data is! Map) return null;
      final data = Map<String, dynamic>.from(resp.data as Map);
      final release = AppRelease.fromJson(data);
      if (release.apkUrl.isEmpty || release.versionCode <= 0) return null;

      final info = await PackageInfo.fromPlatform();
      final current = int.tryParse(info.buildNumber) ?? 0;
      if (current >= release.versionCode) return null; // up to date

      final mandatory = release.forceUpdate || current < release.minVersionCode;
      return UpdateDecision(release: release, mandatory: mandatory);
    } on DioException {
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Downloads the APK to app storage and launches the system installer.
  /// [onProgress] receives (receivedBytes, totalBytes).  Throws on failure.
  Future<void> downloadAndInstall({
    required String apkUrl,
    required void Function(int received, int total) onProgress,
    CancelToken? cancelToken,
  }) async {
    final dir =
        await getExternalStorageDirectory() ?? await getApplicationDocumentsDirectory();
    final filePath = '${dir.path}/qari-update.apk';
    final file = File(filePath);
    if (await file.exists()) await file.delete();

    await _api.dio.download(
      apkUrl,
      filePath,
      cancelToken: cancelToken,
      onReceiveProgress: (received, total) {
        if (total > 0) onProgress(received, total);
      },
    );

    final result = await OpenFilex.open(
      filePath,
      type: 'application/vnd.android.package-archive',
    );
    if (result.type != ResultType.done) {
      throw Exception(result.message.isEmpty ? 'Install failed.' : result.message);
    }
  }
}
