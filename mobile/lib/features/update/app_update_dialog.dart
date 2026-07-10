import 'package:flutter/material.dart';

import 'app_update_service.dart';

/// Modal prompting the user to install an OTA update.
///
/// When [mandatory] is true the dialog cannot be dismissed and the
/// "Later" button is hidden — the user must update before continuing.
class AppUpdateDialog extends StatefulWidget {
  const AppUpdateDialog({
    super.key,
    required this.service,
    required this.release,
    required this.mandatory,
  });

  final AppUpdateService service;
  final AppRelease release;
  final bool mandatory;

  @override
  State<AppUpdateDialog> createState() => _AppUpdateDialogState();
}

class _AppUpdateDialogState extends State<AppUpdateDialog> {
  var _downloading = false;
  var _progress = 0.0;
  String? _error;

  Future<void> _start() async {
    setState(() {
      _downloading = true;
      _error = null;
    });
    try {
      await widget.service.downloadAndInstall(
        apkUrl: widget.release.apkUrl,
        onProgress: (received, total) {
          if (mounted) {
            setState(() => _progress = total > 0 ? received / total : 0.0);
          }
        },
      );
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) {
        setState(() {
          _downloading = false;
          _progress = 0.0;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final note = widget.release.notes['en'] ??
        widget.release.notes.values.firstOrNull ??
        '';
    final percent = (_progress * 100).round();

    return PopScope(
      canPop: !widget.mandatory && !_downloading,
      child: AlertDialog(
        title: Text(widget.mandatory ? 'Update required' : 'Update available'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Version ${widget.release.version} is available.'),
            if (note.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                note,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            if (_downloading) ...[
              const SizedBox(height: 12),
              LinearProgressIndicator(value: _progress),
              const SizedBox(height: 4),
              Text('$percent%'),
            ],
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(
                _error!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
          ],
        ),
        actions: [
          if (!widget.mandatory && !_downloading)
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Later'),
            ),
          FilledButton(
            onPressed: _downloading ? null : _start,
            child: Text(_downloading ? 'Installing…' : 'Update'),
          ),
        ],
      ),
    );
  }
}
