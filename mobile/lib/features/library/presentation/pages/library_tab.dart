import 'package:flutter/material.dart';

import '../../../recitation/presentation/mushaf/mushaf_theme.dart';
import '../../data/library_repository.dart';
import '../library_theme.dart';
import 'library_home_page.dart';

/// The API-backed library environment with the persisted paper preset.
LibraryEnv defaultLibraryEnv() => LibraryEnv(
      repository: ApiLibraryRepository(),
      themeController: MushafThemeController()..load(),
    );

/// The Library as a bottom-navigation tab. Owns its environment for the
/// lifetime of the tab.
class LibraryTab extends StatefulWidget {
  const LibraryTab({super.key, this.envBuilder});

  /// Overridable for tests.
  final LibraryEnv Function()? envBuilder;

  @override
  State<LibraryTab> createState() => _LibraryTabState();
}

class _LibraryTabState extends State<LibraryTab> {
  late final LibraryEnv _env = (widget.envBuilder ?? defaultLibraryEnv)();

  @override
  void dispose() {
    _env.themeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => LibraryHomePage(env: _env);
}
