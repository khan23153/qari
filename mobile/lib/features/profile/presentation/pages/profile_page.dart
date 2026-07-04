import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/services/local_storage_service.dart';

/// S11. Profile/Settings — streak calendar, badges, stats, settings.
class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Stats summary
            _statsCard(context),
            const SizedBox(height: 16),
            // Badges grid
            _badgesSection(context),
            const SizedBox(height: 16),
            // Settings
            _settingsSection(context),
          ],
        ),
      ),
    );
  }

  Widget _statsCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _statItem('7', 'Day Streak', Icons.local_fire_department, Colors.orange),
                _statItem('150', 'Total XP', Icons.star, Colors.amber),
                _statItem('12', 'Lessons', Icons.school, Colors.blue),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statItem(String value, String label, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 32),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }

  Widget _badgesSection(BuildContext context) {
    final badges = [
      {'id': 'streak_7', 'icon': Icons.local_fire_department, 'color': Colors.orange, 'earned': true},
      {'id': 'first_recitation', 'icon': Icons.mic, 'color': Colors.purple, 'earned': true},
      {'id': 'surah_fatihah', 'icon': Icons.book, 'color': Colors.green, 'earned': false},
      {'id': 'streak_30', 'icon': Icons.emoji_events, 'color': Colors.gold, 'earned': false},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Badges', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisSize(
            crossAxisCount: 4,
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
          ),
          itemCount: badges.length,
          itemBuilder: (context, i) {
            final badge = badges[i];
            final earned = badge['earned'] as bool;
            return Container(
              decoration: BoxDecoration(
                color: earned ? (badge['color'] as Color).withOpacity(0.2) : Colors.grey.shade200,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                badge['icon'] as IconData,
                color: earned ? badge['color'] as Color : Colors.grey,
                size: 32,
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _settingsSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Settings', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.language),
                title: const Text('Language'),
                trailing: const Text('Hinglish'),
                onTap: () {},
              ),
              ListTile(
                leading: const Icon(Icons.record_voice_over),
                title: const Text('Qari (Reciter)'),
                trailing: const Text('Alafasy'),
                onTap: () {},
              ),
              ListTile(
                leading: const Icon(Icons.text_fields),
                title: const Text('Arabic Font Size'),
                trailing: Text('${LocalStorageService.instance.fontScale}x'),
                onTap: () => _showFontSizeSlider(context),
              ),
              ListTile(
                leading: const Icon(Icons.palette),
                title: const Text('Theme'),
                trailing: const Text('System'),
                onTap: () {},
              ),
              ListTile(
                leading: const Icon(Icons.download),
                title: const Text('Offline Downloads'),
                onTap: () {},
              ),
              SwitchListTile(
                secondary: const Icon(Icons.mic),
                title: const Text('Audio Training Consent'),
                value: LocalStorageService.instance.audioTrainingConsent,
                onChanged: (v) => setState(() {
                  LocalStorageService.instance.setAudioTrainingConsent(v);
                }),
              ),
              ListTile(
                leading: const Icon(Icons.info),
                title: const Text('Attribution & Licenses'),
                onTap: () {},
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showFontSizeSlider(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Arabic Font Size'),
        content: StatefulBuilder(
          builder: (ctx, setState) {
            double scale = LocalStorageService.instance.fontScale;
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('بِسْمِ اللَّهِ', style: TextStyle(
                  fontFamily: 'QuranUthmani',
                  fontSize: 22 * scale,
                )),
                const SizedBox(height: 16),
                Slider(
                  value: scale,
                  min: 0.8,
                  max: 1.8,
                  divisions: 10,
                  label: '${scale}x',
                  onChanged: (v) => setState(() => scale = v),
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() {});
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}
