import os
from dotenv import load_dotenv
from groq import Groq

# load env vars
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

client = Groq(api_key=GROQ_API_KEY)


def generate_outline(title, notes_before, notes_after=None):
    prompt = f"""
Title: {title}

Editor notes before outline:
{notes_before}

Editor notes after outline:
{notes_after or "None"}

Create a clear book outline with:
- Numbered chapters
- Chapter titles
- Short bullet points per chapter
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1024
    )

    return response.choices[0].message.content


def generate_chapter(
    title,
    outline,
    chapter_number,
    chapter_title,
    previous_summaries,
    chapter_notes=None
):
    prompt = f"""
Book title: {title}

Outline:
{outline}

Previous chapter summaries:
{previous_summaries or "None"}

Now write Chapter {chapter_number}: {chapter_title}

Editor notes for this chapter:
{chapter_notes or "None"}

Write clearly and keep continuity.
End with a short wrap-up for the next chapter.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=2000
    )

    return response.choices[0].message.content


def summarize_chapter(chapter_text):
    prompt = f"""
Summarize the following chapter in 8–12 bullet points.
Focus on key facts, ideas, and concepts.

CHAPTER:
{chapter_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400
    )

    return response.choices[0].message.content