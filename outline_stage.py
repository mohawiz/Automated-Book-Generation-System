from db import supabase
from llm import generate_outline


def process_outlines():
    print("Running outline generation...")

    resp = supabase.table("book_projects").select("*").execute()
    books = resp.data or []

    for book in books:
        book_id = book["id"]
        title = book.get("title")

        notes_before = (book.get("notes_on_outline_before") or "").strip()
        notes_after = (book.get("notes_on_outline_after") or "").strip()
        outline_existing = (book.get("outline") or "").strip()

        # skip if no notes before outline
        if notes_before == "":
            continue

        # skip if outline already exists
        if outline_existing != "":
            print(f"Skipping (outline exists): {title}")
            continue

        print(f"Generating outline for: {title}")

        outline = generate_outline(
            title,
            notes_before,
            notes_after if notes_after != "" else None
        )

        supabase.table("book_projects").update({
            "outline": outline,
            "outline_status": "generated",   # waiting for author approval
            "current_stage": "outline"       # stay here until approved
        }).eq("id", book_id).execute()

        print(f"Outline generated and saved (awaiting review): {title} ✅")