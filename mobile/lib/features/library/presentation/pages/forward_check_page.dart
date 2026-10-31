import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../data/forward_check.dart';
import '../library_theme.dart';
import '../widgets/library_widgets.dart';
import 'hadith_reader_page.dart';

final _arabicScript = RegExp('[؀-ۿ]');

/// Paste a hadith someone forwarded and see whether it is in the hadith
/// collections, with the real wording, its reference and the grades named
/// scholars gave it. Safha never grades: a miss is "not found in these
/// collections", and a failed request is "not checked", never a miss.
class ForwardCheckPage extends StatefulWidget {
  const ForwardCheckPage({super.key, required this.env, this.initialText});

  final LibraryEnv env;

  /// Text to check straight away (e.g. shared into the app).
  final String? initialText;

  @override
  State<ForwardCheckPage> createState() => _ForwardCheckPageState();
}

class _ForwardCheckPageState extends State<ForwardCheckPage> {
  late final TextEditingController _text =
      TextEditingController(text: widget.initialText ?? '');
  bool _checking = false;
  ForwardCheckResult? _result;
  ForwardCheckFailure? _failure;

  bool get _canCheck =>
      !_checking && _text.text.trim().length >= forwardMinLength;

  @override
  void initState() {
    super.initState();
    _text.addListener(() => setState(() {}));
    if (_canCheck)
      WidgetsBinding.instance.addPostFrameCallback((_) => _check());
  }

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Future<void> _paste() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    final pasted = data?.text?.trim();
    if (pasted == null || pasted.isEmpty || !mounted) return;
    _text.text = pasted;
    _text.selection = TextSelection.collapsed(offset: pasted.length);
  }

  Future<void> _check() async {
    if (!_canCheck) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _checking = true;
      _failure = null;
      _result = null;
    });
    final text = _text.text.trim();
    final query = text.length > forwardMaxLength
        ? text.substring(0, forwardMaxLength)
        : text;
    try {
      final result = await widget.env.forwardChecker.check(query);
      if (!mounted) return;
      setState(() => _result = result);
    } on ForwardCheckException catch (e) {
      if (!mounted) return;
      setState(() => _failure = e.failure);
    } catch (_) {
      if (!mounted) return;
      setState(() => _failure = ForwardCheckFailure.unreachable);
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final env = widget.env;
    return LibraryThemed(
      env: env,
      builder: (context, p) => Scaffold(
        backgroundColor: p.paper,
        appBar: AppBar(
          title: Text(
            'Check a forward',
            style: TextStyle(
              color: p.ink,
              fontSize: 19,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
          children: [
            Text(
              'Paste a hadith someone sent you. Safha looks for it in the '
              'hadith collections and shows the real wording, where it is '
              'found and what scholars said about it.',
              style: TextStyle(color: p.muted, fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 14),
            TextField(
              key: const ValueKey('forward-input'),
              controller: _text,
              minLines: 5,
              maxLines: 10,
              maxLength: forwardMaxLength,
              textDirection: _arabicScript.hasMatch(_text.text)
                  ? TextDirection.rtl
                  : TextDirection.ltr,
              style: TextStyle(color: p.ink, fontSize: 16, height: 1.5),
              decoration: const InputDecoration(
                hintText: 'Paste the message here: Arabic, Urdu or English',
                counterText: '',
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                OutlinedButton.icon(
                  key: const ValueKey('forward-paste'),
                  onPressed: _checking ? null : _paste,
                  icon: const Icon(Icons.content_paste_rounded, size: 18),
                  label: const Text('Paste'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: p.ink,
                    side: BorderSide(color: p.border),
                  ),
                ),
                const Spacer(),
                FilledButton(
                  key: const ValueKey('forward-check'),
                  onPressed: _canCheck ? _check : null,
                  style: FilledButton.styleFrom(
                    backgroundColor: p.accent,
                    foregroundColor: p.onAccent,
                    disabledBackgroundColor: p.card,
                    disabledForegroundColor: p.muted,
                  ),
                  child: const Text('Check'),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_checking)
              _Searching(palette: p)
            else if (_failure != null)
              _FailureCard(failure: _failure!, palette: p, onRetry: _check)
            else if (_result != null)
              _ResultView(result: _result!, env: env, palette: p),
          ],
        ),
      ),
    );
  }
}

class _Searching extends StatelessWidget {
  const _Searching({required this.palette});

  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 12),
          Text(
            'Searching the collections…',
            style: TextStyle(color: palette.muted, fontSize: 14),
          ),
        ],
      ),
    );
  }
}

/// The message was NOT checked. Worded so it can never read as "not found".
class _FailureCard extends StatelessWidget {
  const _FailureCard({
    required this.failure,
    required this.palette,
    required this.onRetry,
  });

  final ForwardCheckFailure failure;
  final LibraryPalette palette;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final (IconData icon, String title, String body) = switch (failure) {
      ForwardCheckFailure.preparing => (
          Icons.hourglass_top_rounded,
          'Getting the collections ready',
          'Safha is preparing the collections for checking. Try again in a '
              'minute.',
        ),
      ForwardCheckFailure.invalidText => (
          Icons.short_text_rounded,
          'Paste a little more',
          'Safha needs a few words of the hadith to compare.',
        ),
      ForwardCheckFailure.unreachable => (
          Icons.cloud_off_rounded,
          "Couldn't check this message",
          "Safha's server could not be reached, so nothing was searched. "
              'Check your connection and try again.',
        ),
    };
    return Container(
      key: ValueKey('forward-failure-${failure.name}'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: p.muted),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: p.ink,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(body,
              style: TextStyle(color: p.muted, fontSize: 14, height: 1.4)),
          if (failure != ForwardCheckFailure.invalidText) ...[
            const SizedBox(height: 6),
            TextButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ],
      ),
    );
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({
    required this.result,
    required this.env,
    required this.palette,
  });

  final ForwardCheckResult result;
  final LibraryEnv env;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final searched = result.searchedCollections;
    final searchedLine = searched.isEmpty
        ? null
        : Text(
            'Searched: ${searched.join(', ')}',
            key: const ValueKey('forward-searched'),
            style: TextStyle(color: p.muted, fontSize: 12, height: 1.4),
          );

    if (result.matches.isEmpty) {
      return Container(
        key: const ValueKey('forward-not-found'),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: p.card,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: p.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.search_off_rounded, color: p.muted),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Not found in these collections',
                    style: TextStyle(
                      color: p.ink,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              result.note,
              style: TextStyle(color: p.ink, fontSize: 14, height: 1.4),
            ),
            if (searchedLine != null) ...[
              const SizedBox(height: 10),
              searchedLine,
            ],
          ],
        ),
      );
    }

    final anyStrong = result.matches.any((m) => m.band == ForwardBand.strong);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          anyStrong ? 'Found in the collections' : 'Possible matches',
          style: TextStyle(
            color: p.ink,
            fontSize: 17,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          result.note,
          style: TextStyle(color: p.muted, fontSize: 13, height: 1.4),
        ),
        const SizedBox(height: 12),
        for (final m in result.matches) ...[
          _MatchCard(match: m, env: env, palette: p),
          const SizedBox(height: 12),
        ],
        if (searchedLine != null) searchedLine,
      ],
    );
  }
}

class _MatchCard extends StatelessWidget {
  const _MatchCard({
    required this.match,
    required this.env,
    required this.palette,
  });

  final ForwardMatch match;
  final LibraryEnv env;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final h = match.hadith;
    final strong = match.band == ForwardBand.strong;
    final collection =
        match.collectionName.isEmpty ? h.collection : match.collectionName;
    return Container(
      key: ValueKey('forward-match-${h.id}'),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: strong ? p.accent.withValues(alpha: 0.6) : p.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '$collection #${h.number}',
                  style: TextStyle(
                    color: p.ink,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: strong ? p.badge(p.accent) : p.paper,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: strong ? p.accent.withValues(alpha: 0.55) : p.border,
                  ),
                ),
                child: Text(
                  strong ? 'Close wording' : 'Partly similar',
                  style: TextStyle(
                    color: strong ? p.accent : p.muted,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            h.matnAr,
            textDirection: TextDirection.rtl,
            style: TextStyle(
              color: p.ink,
              fontSize: 21,
              height: 1.8,
              fontFamily: libraryArabicFont,
            ),
          ),
          if (h.translationText != null) ...[
            const SizedBox(height: 6),
            Text(
              h.translationText!,
              style: TextStyle(color: p.ink, fontSize: 14, height: 1.45),
            ),
          ],
          const SizedBox(height: 12),
          Text(
            'What scholars said',
            style: TextStyle(
              color: p.muted,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          GradeBadges(grades: h.grades, palette: p),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => HadithReaderPage(env: env, hadithId: h.id),
                ),
              ),
              child: Text(
                'Open in Library',
                style: TextStyle(color: p.accent),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
