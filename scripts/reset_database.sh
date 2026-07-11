#!/usr/bin/env bash
# reset_database.sh — Wipe all Qari user/account data and reload fresh seed data.
#
# What it does (default):
#   1. TRUNCATE all user/account/progress tables (CASCADE)
#   2. TRUNCATE seed tables (qaris, badges, lessons, quiz_questions) and re-seed them
#   3. Flush the Redis recitation job stream and recreate the consumer group
#   4. Restart the inference worker so it picks up the fresh stream
#
# The Quran corpus (surahs/ayahs/words/tajweed/roots) is NOT touched by default
# because it is already loaded and correct. To ALSO wipe and re-import the full
# corpus via the ETL pipeline, pass --with-corpus (requires network + the
# QURANIC_CORPUS_FILE morphology file).
#
# Usage:
#   ./reset_database.sh            # wipe users + reseed dev data
#   ./reset_database.sh --with-corpus   # also re-run the full ETL corpus load
#   ./reset_database.sh --hard      # wipe EVERYTHING including corpus tables
#
set -euo pipefail

PG="docker exec -i infra-postgres-1 psql -U qari -d qari -v ON_ERROR_STOP=1"
REDIS="docker exec -i infra-redis-1 redis-cli"

WITH_CORPUS=0
HARD=0
for arg in "$@"; do
  case "$arg" in
    --with-corpus) WITH_CORPUS=1 ;;
    --hard) HARD=1 ;;
  esac
done

echo "🧹 Resetting Qari database..."

# --- 1. User / account / progress tables (always wiped) ---
USER_TABLES="user_lesson_progress, user_ayah_progress, flashcard_reviews, flashcards, \
user_stats, user_badges, recitation_word_results, recitation_sessions, scholar_questions, users"
echo "  • truncating user tables..."
$PG -c "TRUNCATE TABLE $USER_TABLES RESTART IDENTITY CASCADE;"

# --- 2. Seed tables ---
SEED_TABLES="quiz_questions, lessons, badges, qaris"
echo "  • truncating seed tables..."
$PG -c "TRUNCATE TABLE $SEED_TABLES RESTART IDENTITY CASCADE;"

# --- 3. Corpus tables (only with --hard / --with-corpus) ---
if [ "$HARD" = "1" ] || [ "$WITH_CORPUS" = "1" ]; then
  CORPUS_TABLES="tajweed_annotations, words, roots, ayahs, surahs"
  echo "  • truncating corpus tables..."
  $PG -c "TRUNCATE TABLE $CORPUS_TABLES RESTART IDENTITY CASCADE;"
fi

# --- 4. Redis recitation stream ---
echo "  • clearing Redis recitation stream..."
$REDIS DEL qari:recitation:jobs >/dev/null 2>&1 || true

# --- 5. Re-seed dev data (qaris, badges, lessons) ---
echo "  • re-seeding dev data..."
docker exec -e DATABASE_URL="postgresql+asyncpg://qari:qari@postgres:5432/qari" \
  infra-core-api-1 python seed_dev_data.py

# --- 6. Restart inference worker (recreates the Redis consumer group) ---
echo "  • restarting inference worker..."
docker restart infra-inference-worker-1 >/dev/null

# --- 7. Optionally re-run the full ETL corpus load ---
if [ "$WITH_CORPUS" = "1" ] || [ "$HARD" = "1" ]; then
  echo "  • running full ETL corpus pipeline..."
  docker exec -e DATABASE_URL="postgresql+asyncpg://qari:qari@postgres:5432/qari" \
    infra-core-api-1 python -m etl.run_full_pipeline
fi

echo "✅ Reset complete."
echo "   NOTE: Any 'half-complete' progress shown in the app is stored LOCALLY on your"
echo "   device, not in this database. To clear it, clear the app's storage or"
echo "   reinstall the app (Settings → Apps → Qari → Clear storage / uninstall)."
