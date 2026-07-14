import 'package:flutter/material.dart';

/// App-wide root navigator key.
///
/// Using this (instead of capturing a widget's `BuildContext`) lets screens
/// navigate from callbacks that may outlive the widget that created them —
/// e.g. the "Reset & Start Fresh" flow, where the post-auth navigation must
/// survive after the Profile screen that triggered the reset is removed.
final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();
