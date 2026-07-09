import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Provider for the current app theme mode.
final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);

/// Provider for the current app locale.
final appLocaleProvider = StateProvider<Locale>((ref) => const Locale('en'));
