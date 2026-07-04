import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/lesson_model.dart';

/// Quiz widget — supports MCQ, drag-match, and fill-blank question types.
/// Shows immediate feedback with haptics after answering.
class QuizWidget extends StatefulWidget {
  final QuizQuestionModel question;
  final void Function(bool isCorrect) onAnswered;

  const QuizWidget({
    super.key,
    required this.question,
    required this.onAnswered,
  });

  @override
  State<QuizWidget> createState() => _QuizWidgetState();
}

class _QuizWidgetState extends State<QuizWidget> {
  String? _selectedAnswer;
  bool? _isCorrect;
  final TextEditingController _fillBlankController = TextEditingController();
  final Map<String, String> _matchAnswers = {};

  @override
  void dispose() {
    _fillBlankController.dispose();
    super.dispose();
  }

  void _submitMCQ(String answer) {
    if (_isCorrect != null) return; // Already answered

    setState(() {
      _selectedAnswer = answer;
      _isCorrect = answer == widget.question.correctAnswer;
    });

    if (_isCorrect!) {
      Haptics.impact();
    } else {
      Haptics.heavyImpact();
    }

    widget.onAnswered(_isCorrect!);
  }

  void _submitFillBlank() {
    if (_isCorrect != null) return;

    final answer = _fillBlankController.text.trim().toLowerCase();
    final correct = widget.question.blankAnswer?.toLowerCase() ?? '';
    final isCorrect = answer == correct || answer.contains(correct);

    setState(() => _isCorrect = isCorrect);

    if (isCorrect) {
      Haptics.impact();
    } else {
      Haptics.heavyImpact();
    }

    widget.onAnswered(isCorrect);
  }

  void _submitDragMatch() {
    if (_isCorrect != null) return;

    bool allCorrect = true;
    for (final pair in widget.question.matchPairs ?? []) {
      if (_matchAnswers[pair.left] != pair.right) {
        allCorrect = false;
        break;
      }
    }

    setState(() => _isCorrect = allCorrect);

    if (allCorrect) {
      Haptics.impact();
    } else {
      Haptics.heavyImpact();
    }

    widget.onAnswered(allCorrect);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Question label
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: theme.colorScheme.secondary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              _typeLabel(widget.question.type),
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.secondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Question text
          Text(
            widget.question.question,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          if (widget.question.questionArabic != null) ...[
            const SizedBox(height: 8),
            Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                widget.question.questionArabic!,
                style: AppTheme.arabicTextStyle(fontSize: 28),
              ),
            ),
          ],

          const SizedBox(height: 24),

          // Answer area based on type
          Expanded(
            child: _buildAnswerArea(context),
          ),

          // Feedback
          if (_isCorrect != null) ...[
            const SizedBox(height: 16),
            _FeedbackBanner(isCorrect: _isCorrect!, explanation: widget.question.explanation),
          ],
        ],
      ),
    );
  }

  Widget _buildAnswerArea(BuildContext context) {
    switch (widget.question.type) {
      case QuizType.mcq:
      case QuizType.trueFalse:
        return _buildMCQ(context);
      case QuizType.dragMatch:
        return _buildDragMatch(context);
      case QuizType.fillBlank:
        return _buildFillBlank(context);
    }
  }

  Widget _buildMCQ(BuildContext context) {
    final theme = Theme.of(context);
    final options = widget.question.type == QuizType.trueFalse
        ? ['True', 'False']
        : widget.question.options;

    return ListView.separated(
      itemCount: options.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final option = options[index];
        final isSelected = _selectedAnswer == option;
        final showCorrect = _isCorrect != null && option == widget.question.correctAnswer;
        final showWrong = isSelected && _isCorrect == false;

        return Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: _isCorrect == null ? () => _submitMCQ(option) : null,
            borderRadius: BorderRadius.circular(12),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: showCorrect
                    ? theme.colorScheme.primary.withValues(alpha: 0.1)
                    : showWrong
                        ? theme.colorScheme.error.withValues(alpha: 0.1)
                        : theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: showCorrect
                      ? theme.colorScheme.primary
                      : showWrong
                          ? theme.colorScheme.error
                          : theme.colorScheme.outline.withValues(alpha: 0.2),
                  width: showCorrect || showWrong ? 2 : 1,
                ),
              ),
              child: Row(
                children: [
                  // Option letter
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: showCorrect
                          ? theme.colorScheme.primary
                          : showWrong
                              ? theme.colorScheme.error
                              : theme.colorScheme.outline.withValues(alpha: 0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: showCorrect
                          ? const Icon(Icons.check_rounded, color: Colors.white, size: 18)
                          : showWrong
                              ? const Icon(Icons.close_rounded, color: Colors.white, size: 18)
                              : Text(
                                  String.fromCharCode(65 + index),
                                  style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                                  ),
                                ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      option,
                      style: theme.textTheme.bodyLarge,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildFillBlank(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _fillBlankController,
          enabled: _isCorrect == null,
          decoration: const InputDecoration(
            hintText: 'Type your answer...',
            prefixIcon: Icon(Icons.edit_rounded),
          ),
          onSubmitted: (_) => _submitFillBlank(),
        ),
        const SizedBox(height: 16),
        if (_isCorrect == null)
          FilledButton(
            onPressed: _submitFillBlank,
            child: const Text('Submit'),
          ),
        if (_isCorrect != null)
          Text(
            'Answer: ${widget.question.blankAnswer}',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
      ],
    );
  }

  Widget _buildDragMatch(BuildContext context) {
    final theme = Theme.of(context);
    final pairs = widget.question.matchPairs ?? [];
    final leftItems = pairs.map((p) => p.left).toList();
    final rightItems = pairs.map((p) => p.right).toList()..shuffle();

    return Column(
      children: [
        // Left column (Arabic) — tap to select, then tap right to match
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Left items
              Expanded(
                child: Column(
                  children: leftItems.map((left) {
                    final matched = _matchAnswers.containsKey(left);
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: _MatchTile(
                        text: left,
                        isArabic: true,
                        isMatched: matched,
                        matchValue: _matchAnswers[left],
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(width: 12),
              // Right items
              Expanded(
                child: Column(
                  children: rightItems.map((right) {
                    final used = _matchAnswers.containsValue(right);
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: _MatchTile(
                        text: right,
                        isArabic: false,
                        isMatched: used,
                        onTap: _isCorrect == null
                            ? () => _onRightTap(right)
                            : null,
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ),
        if (_isCorrect == null && _matchAnswers.length == pairs.length)
          Padding(
            padding: const EdgeInsets.only(top: 16),
            child: FilledButton(
              onPressed: _submitDragMatch,
              child: const Text('Check Answers'),
            ),
          ),
      ],
    );
  }

  String? _selectedLeft;

  void _onRightTap(String right) {
    // Simple matching: cycle through unmatched left items
    final pairs = widget.question.matchPairs ?? [];
    for (final pair in pairs) {
      if (!_matchAnswers.containsKey(pair.left)) {
        setState(() {
          _matchAnswers[pair.left] = right;
        });
        break;
      }
    }
  }

  String _typeLabel(QuizType type) {
    switch (type) {
      case QuizType.mcq:
        return 'Multiple Choice';
      case QuizType.dragMatch:
        return 'Match the Pairs';
      case QuizType.fillBlank:
        return 'Fill in the Blank';
      case QuizType.trueFalse:
        return 'True or False';
    }
  }
}

/// A tile for drag-match questions.
class _MatchTile extends StatelessWidget {
  final String text;
  final bool isArabic;
  final bool isMatched;
  final String? matchValue;
  final VoidCallback? onTap;

  const _MatchTile({
    required this.text,
    required this.isArabic,
    required this.isMatched,
    this.matchValue,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isMatched
                ? theme.colorScheme.primary.withValues(alpha: 0.08)
                : theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isMatched
                  ? theme.colorScheme.primary.withValues(alpha: 0.3)
                  : theme.colorScheme.outline.withValues(alpha: 0.2),
            ),
          ),
          child: isArabic
              ? Directionality(
                  textDirection: TextDirection.rtl,
                  child: Column(
                    children: [
                      Text(
                        text,
                        style: AppTheme.arabicTextStyle(fontSize: 24),
                        textAlign: TextAlign.center,
                      ),
                      if (matchValue != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          '→ $matchValue',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ],
                  ),
                )
              : Text(
                  text,
                  style: theme.textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
        ),
      ),
    );
  }
}

/// Feedback banner shown after answering.
class _FeedbackBanner extends StatelessWidget {
  final bool isCorrect;
  final String? explanation;

  const _FeedbackBanner({required this.isCorrect, this.explanation});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = isCorrect ? theme.colorScheme.primary : theme.colorScheme.error;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isCorrect ? Icons.check_circle_rounded : Icons.cancel_rounded,
            color: color,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isCorrect ? 'Correct!' : 'Not quite right',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (explanation != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    explanation!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 300.ms)
        .slideY(begin: 0.1, end: 0);
  }
}
