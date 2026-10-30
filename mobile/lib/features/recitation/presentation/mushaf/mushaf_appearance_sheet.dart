import 'package:flutter/material.dart';

import 'mushaf_theme.dart';

/// The live page's "Display" sheet: the tajweed-colour switch and the entry
/// into the page-theme picker.
///
/// The sheet is opened from the page's own `State.context`, which sits ABOVE
/// the page's local `Theme(data: mushaf.toThemeData())`. A modal route only
/// captures themes from that context, so without the explicit [Theme] below
/// its children resolved colours from the app-wide theme (dark card, light
/// list-tile ink) while the sheet itself painted the Mushaf paper. Every
/// colour here is therefore resolved from [theme].
class MushafAppearanceSheet extends StatefulWidget {
  const MushafAppearanceSheet({
    super.key,
    required this.theme,
    required this.tajweedOn,
    required this.onTajweedChanged,
    required this.onPageTheme,
  });

  final MushafTheme theme;
  final bool tajweedOn;
  final ValueChanged<bool> onTajweedChanged;

  /// Called after the sheet closes itself, to open the theme picker.
  final VoidCallback onPageTheme;

  static Future<void> show(
    BuildContext context, {
    required MushafTheme theme,
    required bool tajweedOn,
    required ValueChanged<bool> onTajweedChanged,
    required VoidCallback onPageTheme,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      backgroundColor: theme.background,
      useSafeArea: true,
      builder: (_) => MushafAppearanceSheet(
        theme: theme,
        tajweedOn: tajweedOn,
        onTajweedChanged: onTajweedChanged,
        onPageTheme: onPageTheme,
      ),
    );
  }

  @override
  State<MushafAppearanceSheet> createState() => _MushafAppearanceSheetState();
}

class _MushafAppearanceSheetState extends State<MushafAppearanceSheet> {
  late bool _tajweedOn = widget.tajweedOn;

  @override
  Widget build(BuildContext context) {
    final t = widget.theme;
    return Theme(
      data: t.toThemeData(),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            MushafTajweedToggle(
              theme: t,
              value: _tajweedOn,
              onChanged: (value) {
                setState(() => _tajweedOn = value);
                widget.onTajweedChanged(value);
              },
            ),
            const SizedBox(height: 12),
            ListTile(
              key: const ValueKey('mushaf-appearance-page-theme'),
              leading: Icon(Icons.palette_outlined, color: t.mutedInk),
              title: Text('Page theme', style: TextStyle(color: t.text)),
              trailing: Icon(Icons.chevron_right_rounded, color: t.mutedInk),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              onTap: () {
                Navigator.of(context).pop();
                widget.onPageTheme();
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// Inline toggle for live per-letter tajweed colouring.
///
/// The card is a tint of the current paper ([MushafTheme.card]), never a
/// fixed dark block, and the switch's inactive thumb/outline use
/// [MushafTheme.mutedInk] so the "off" state stays visible on cream paper.
class MushafTajweedToggle extends StatelessWidget {
  const MushafTajweedToggle({
    super.key,
    required this.theme,
    required this.value,
    required this.onChanged,
  });

  final MushafTheme theme;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = theme;
    return Material(
      key: const ValueKey('mushaf-tajweed-card'),
      color: value
          ? Color.alphaBlend(t.accent.withValues(alpha: 0.10), t.card)
          : t.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: value ? t.accent.withValues(alpha: 0.55) : t.border,
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => onChanged(!value),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Icon(
                Icons.palette_rounded,
                size: 20,
                color: value ? t.accent : t.mutedInk,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Tajweed colours',
                      style: TextStyle(
                        color: t.text,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Colour each letter by its tajweed rule as it appears',
                      style: TextStyle(color: t.mutedInk, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Switch(
                key: const ValueKey('mushaf-tajweed-switch'),
                value: value,
                onChanged: onChanged,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
