import 'package:flutter/material.dart';

/// Attribution & licenses page — credits for fonts, audio sources,
/// open-source libraries, and data sources.
class AttributionPage extends StatelessWidget {
  const AttributionPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Attribution & Licenses'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ─── Quran Text ────────────────────────────────────────────
          _AttributionSection(
            title: 'Quran Text & Data',
            theme: theme,
            items: [
              _AttributionItem(
                name: 'KFGQPC Uthmanic Hafs',
                description: 'Quranic text font (Uthmanic Hafs narration)',
                license: 'King Fahd Glorious Quran Printing Complex',
              ),
              _AttributionItem(
                name: 'Tanzil.net',
                description: 'Quran text corpus and metadata',
                license: 'Tanzil Project License',
              ),
              _AttributionItem(
                name: 'Quran.com API',
                description: 'Ayah text, translations, and audio URLs',
                license: 'Quran.com',
              ),
            ],
          ),

          const SizedBox(height: 24),

          // ─── Translations ──────────────────────────────────────────
          _AttributionSection(
            title: 'Translations',
            theme: theme,
            items: [
              _AttributionItem(
                name: 'Sahih International (English)',
                description: 'English translation of the Quran',
                license: 'Sahih International',
              ),
              _AttributionItem(
                name: 'Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan (English)',
                description: 'English translation with commentary',
                license: 'Dar-us-Salam Publications',
              ),
              _AttributionItem(
                name: 'Maududi (Urdu)',
                description: 'Urdu translation and tafsir',
                license: 'Islamic Publications',
              ),
            ],
          ),

          const SizedBox(height: 24),

          // ─── Audio ─────────────────────────────────────────────────
          _AttributionSection(
            title: 'Recitation Audio',
            theme: theme,
            items: [
              _AttributionItem(
                name: 'Abdul Basit Abdus-Samad',
                description: 'Full Quran recitation (Mujawwad)',
                license: 'Public domain / Quranic Audio',
              ),
              _AttributionItem(
                name: 'Abdul Rahman Al-Sudais',
                description: 'Full Quran recitation',
                license: 'Quran.com Audio',
              ),
              _AttributionItem(
                name: 'Al-Minshawi',
                description: 'Full Quran recitation (Mujawwad)',
                license: 'Quranic Audio',
              ),
              _AttributionItem(
                name: 'Al-Husary',
                description: 'Full Quran recitation',
                license: 'Quranic Audio',
              ),
              _AttributionItem(
                name: 'Mishary Rashid Al-Afasy',
                description: 'Full Quran recitation',
                license: 'Quran.com Audio',
              ),
            ],
          ),

          const SizedBox(height: 24),

          // ─── Fonts ─────────────────────────────────────────────────
          _AttributionSection(
            title: 'Fonts',
            theme: theme,
            items: [
              _AttributionItem(
                name: 'Noto Sans',
                description: 'UI text font for Latin and multiple scripts',
                license: 'SIL Open Font License 1.1',
              ),
              _AttributionItem(
                name: 'Noto Nastaliq Urdu',
                description: 'Urdu text rendering (Nastaliq script)',
                license: 'SIL Open Font License 1.1',
              ),
              _AttributionItem(
                name: 'KFGQPC Uthmanic Hafs',
                description: 'Arabic Quranic text font',
                license: 'KFGQPC',
              ),
            ],
          ),

          const SizedBox(height: 24),

          // ─── Open Source Libraries ─────────────────────────────────
          _AttributionSection(
            title: 'Open Source Libraries',
            theme: theme,
            items: [
              _AttributionItem(
                name: 'Flutter',
                description: 'UI framework',
                license: 'BSD 3-Clause License',
              ),
              _AttributionItem(
                name: 'Riverpod',
                description: 'State management',
                license: 'MIT License',
              ),
              _AttributionItem(
                name: 'Dio',
                description: 'HTTP client',
                license: 'MIT License',
              ),
              _AttributionItem(
                name: 'just_audio',
                description: 'Audio playback',
                license: 'Apache 2.0 License',
              ),
              _AttributionItem(
                name: 'record',
                description: 'Audio recording',
                license: 'MIT License',
              ),
              _AttributionItem(
                name: 'Freezed',
                description: 'Model code generation',
                license: 'MIT License',
              ),
              _AttributionItem(
                name: 'fl_chart',
                description: 'Chart rendering',
                license: 'FL Chart License',
              ),
              _AttributionItem(
                name: 'flutter_animate',
                description: 'UI animations',
                license: 'BSD 3-Clause License',
              ),
            ],
          ),

          const SizedBox(height: 24),

          // ─── Disclaimer ────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.info_outline_rounded, color: theme.colorScheme.primary, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Disclaimer',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'The Quran text and translations in this app are provided for educational purposes. '
                  'For official religious rulings (fatwas), please consult a qualified scholar. '
                  'While we strive for accuracy, we are not responsible for any errors in text or translation.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    height: 1.6,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          // ─── Copyright ─────────────────────────────────────────────
          Center(
            child: Text(
              '© 2026 Qari App. All Quran data belongs to the public domain.',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.3),
              ),
              textAlign: TextAlign.center,
            ),
          ),

          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

/// Attribution section with a title and list of items.
class _AttributionSection extends StatelessWidget {
  final String title;
  final ThemeData theme;
  final List<_AttributionItem> items;

  const _AttributionSection({
    required this.title,
    required this.theme,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 12),
        ...items.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: theme.colorScheme.outline.withValues(alpha: 0.1),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: theme.textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      item.description,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        item.license,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.primary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )),
      ],
    );
  }
}

/// Attribution item data.
class _AttributionItem {
  final String name;
  final String description;
  final String license;

  const _AttributionItem({
    required this.name,
    required this.description,
    required this.license,
  });
}
