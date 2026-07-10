"""Seed database with sample data for development."""
import asyncio
import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://qari:qari@localhost:5432/qari"


async def seed():
    engine = create_async_engine(DB_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # Seed qaris
        qaris = [
            (1, "Mishary Rashid Alafasy", "murattal", "https://cdn.qari.app/audio/alafasy/", True),
            (2, "Abdul Basit", "murattal", "https://cdn.qari.app/audio/abdulbasit/", False),
            (3, "Husary", "murattal", "https://cdn.qari.app/audio/husary/", False),
        ]
        for q in qaris:
            await db.execute(text("""
                INSERT INTO qaris (qari_id, name, style, base_audio_url, is_default)
                VALUES (:id, :name, :style, :url, :default)
                ON CONFLICT (qari_id) DO NOTHING
            """), {"id": q[0], "name": q[1], "style": q[2], "url": q[3], "default": q[4]})

        # Seed badges
        badges = [
            ("streak_7", {"en": "7 Day Streak", "hi_latn": "7 din streak"},
             {"en": "Study 7 days in a row", "hi_latn": "7 din lagatar padhein"},
             "https://cdn.qari.app/badges/streak_7.png",
             {"type": "streak", "days": 7}),
            ("first_recitation", {"en": "First Recitation", "hi_latn": "Pehli tilawat"},
             {"en": "Complete your first AI recitation", "hi_latn": "Apni pehli AI tilawat karein"},
             "https://cdn.qari.app/badges/first_recitation.png",
             {"type": "xp", "amount": 0}),
            ("streak_30", {"en": "30 Day Streak", "hi_latn": "30 din streak"},
             {"en": "Study 30 days in a row", "hi_latn": "30 din lagatar padhein"},
             "https://cdn.qari.app/badges/streak_30.png",
             {"type": "streak", "days": 30}),
        ]
        for b in badges:
            await db.execute(text("""
                INSERT INTO badges (badge_id, title, description, icon_url, criteria)
                VALUES (:id, :title, :desc, :icon, :crit)
                ON CONFLICT (badge_id) DO NOTHING
            """), {
                "id": b[0], "title": json.dumps(b[1]),
                "desc": json.dumps(b[2]), "icon": b[3],
                "crit": json.dumps(b[4]),
            })

        # Seed sample lessons (Module 1)
        lessons = [
            (1, 1, 1, "alphabet",
             {"en": "Arabic Alphabet: Alif, Baa, Taa", "hi_latn": "Arabi Alphabet: Alif, Baa, Taa"},
             {"type": "alphabet", "letters": ["ا", "ب", "ت"]}, 10),
            (1, 1, 2, "makhraj",
             {"en": "Makhraj: Where Sounds Come From", "hi_latn": "Makhraj: Awaaz kahan se aati hai"},
             {"type": "makhraj", "video_url": "makhraj_intro.mp4"}, 15),
            (1, 1, 3, "grammar_card",
             {"en": "Ism, Fi'l, Harf — Three Word Types", "hi_latn": "Ism, Fi'l, Harf — Teen tarah ke lafz"},
             {"type": "grammar_card", "concept": "word_types"}, 10),
        ]
        for l in lessons:
            await db.execute(text("""
                INSERT INTO lessons (lesson_id, module, unit_number, sequence, lesson_type,
                    title, content, xp_reward, review_status)
                VALUES (:id, :mod, :unit, :seq, :type, :title, :content, :xp, 'published')
                ON CONFLICT (module, unit_number, sequence) DO NOTHING
            """), {
                "id": str(uuid4()), "mod": l[0], "unit": l[1], "seq": l[2],
                "type": l[3], "title": json.dumps(l[4]),
                "content": json.dumps(l[5]), "xp": l[6],
            })

        await db.commit()

    await engine.dispose()
    print("✅ Seed data inserted: 3 qaris, 3 badges, 3 lessons")


if __name__ == "__main__":
    asyncio.run(seed())
