"""Seed database with sample data for development.

Columns are kept in sync with the current SQLAlchemy models in
``app/models/corpus.py`` (Qari) and ``app/models/content.py`` (Badge, Lesson).
"""

import asyncio
import json
import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://qari:qari@localhost:5432/qari")


async def seed():
    engine = create_async_engine(DB_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # --- Qaris (reciters) ---
        qaris = [
            (1, "Mishary Rashid Alafasy", "مشاري راشد العفاسي", "murattal",
             "https://cdn.qari.app/audio/alafasy/", True),
            (2, "Abdul Basit", "عبد الباسط عبد الصمد", "murattal",
             "https://cdn.qari.app/audio/abdulbasit/", False),
            (3, "Husary", "محمود خليل الحصري", "murattal",
             "https://cdn.qari.app/audio/husary/", False),
        ]
        for q in qaris:
            await db.execute(text("""
                INSERT INTO qaris (id, name, arabic_name, style, audio_base_url, is_active)
                VALUES (:id, :name, :arabic_name, :style, :url, :active)
                ON CONFLICT (id) DO NOTHING
            """), {"id": q[0], "name": q[1], "arabic_name": q[2], "style": q[3],
                   "url": q[4], "active": q[5]})

        # --- Badges ---
        badges = [
            ("streak_7", "7 Day Streak", "7 Din Streak", "7 دن کی سلسلہ بندی",
             "Study 7 days in a row", "7 din lagatar padhein",
             "https://cdn.qari.app/badges/streak_7.png", "bronze", 0,
             json.dumps({"type": "streak", "days": 7})),
            ("first_recitation", "First Recitation", "Pehli Tilawat", "پہلی تلاوت",
             "Complete your first AI recitation", "Apni pehli AI tilawat karein",
             "https://cdn.qari.app/badges/first_recitation.png", "bronze", 0,
             json.dumps({"type": "xp", "amount": 0})),
            ("streak_30", "30 Day Streak", "30 Din Streak", "30 دن کی سلسلہ بندی",
             "Study 30 days in a row", "30 din lagatar padhein",
             "https://cdn.qari.app/badges/streak_30.png", "silver", 0,
             json.dumps({"type": "streak", "days": 30})),
        ]
        for b in badges:
            await db.execute(text("""
                INSERT INTO badges (slug, name_en, name_hi_latn, name_ur,
                    description_en, description_hi_latn, icon_url, tier, xp_reward, criteria_json)
                VALUES (:slug, :name_en, :name_hi_latn, :name_ur,
                    :desc_en, :desc_hi_latn, :icon, :tier, :xp, :crit)
                ON CONFLICT (slug) DO NOTHING
            """), {
                "slug": b[0], "name_en": b[1], "name_hi_latn": b[2], "name_ur": b[3],
                "desc_en": b[4], "desc_hi_latn": b[5], "icon": b[6],
                "tier": b[7], "xp": b[8], "crit": b[9],
            })

        # --- Lessons (Module 1: alphabet + foundations) ---
        lessons = [
            ("m1-u1-l1", "alphabet", "Arabic Alphabet: Alif, Baa, Taa",
             "अरबी अल्फाबेट: अलिफ, बा, ता", "عربی حروف: الف، ب، ت",
             "Learn the first three Arabic letters and their shapes.",
             json.dumps({"type": "alphabet", "letters": ["ا", "ب", "ت"]}), 1, 10, "published"),
            ("m1-u1-l2", "makhraj", "Makhraj: Where Sounds Come From",
             "मखरज: आवाज़ कहाँ से आती है", "مخرج: آواز کہاں سے آتی ہے",
             "Understand the articulation points of Arabic letters.",
             json.dumps({"type": "makhraj", "video_url": "makhraj_intro.mp4"}), 2, 15, "published"),
            ("m1-u1-l3", "grammar_card", "Ism, Fi'l, Harf — Three Word Types",
             "इस्म, फ़ि'ल, हर्फ़ — तीन तरह के लफ़्ज़", "اسم، فعل، حرف — تین قسم کے الفاظ",
             "The three fundamental word types in Arabic grammar.",
             json.dumps({"type": "grammar_card", "concept": "word_types"}), 3, 10, "published"),
        ]
        for l in lessons:
            await db.execute(text("""
                INSERT INTO lessons (slug, module, title_en, title_hi_latn, title_ur,
                    summary_en, content_en, lesson_order, xp_reward, review_status)
                VALUES (:slug, :module, :title_en, :title_hi_latn, :title_ur,
                    :summary_en, :content_en, :order, :xp, :status)
                ON CONFLICT (slug) DO NOTHING
            """), {
                "slug": l[0], "module": l[1], "title_en": l[2], "title_hi_latn": l[3],
                "title_ur": l[4], "summary_en": l[5], "content_en": l[6],
                "order": l[7], "xp": l[8], "status": l[9],
            })

        await db.commit()

    await engine.dispose()
    print("✅ Seed data inserted: 3 qaris, 3 badges, 3 lessons")


if __name__ == "__main__":
    asyncio.run(seed())
