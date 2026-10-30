import 'package:flutter/material.dart';

import '../../../recitation/presentation/mushaf/mushaf_theme.dart';
import '../../data/library_repository.dart';
import '../library_theme.dart';
import '../pages/library_home_page.dart';

/// Home-screen entry into the Islamic Library. Styled with the app theme (it
/// lives on Home); the library itself uses the Mushaf paper presets.
class LibraryEntryCard extends StatelessWidget {
  const LibraryEntryCard({super.key, this.envBuilder});

  /// Overridable for tests; production builds an API-backed env and loads the
  /// persisted paper preset.
  final LibraryEnv Function()? envBuilder;

  LibraryEnv _defaultEnv() => LibraryEnv(
        repository: ApiLibraryRepository(),
        themeController: MushafThemeController()..load(),
      );

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(18),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        key: const ValueKey('library-entry-card'),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => LibraryHomePage(env: (envBuilder ?? _defaultEnv)()),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: scheme.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.local_library_rounded, color: scheme.primary),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Islamic Library',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: scheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Hadith with scholar grades, isnad and narrators',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: scheme.onSurface.withValues(alpha: 0.7),
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: scheme.onSurface.withValues(alpha: 0.6)),
            ],
          ),
        ),
      ),
    );
  }
}
