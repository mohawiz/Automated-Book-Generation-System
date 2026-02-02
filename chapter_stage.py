import re
from db import supabase
from llm import generate_chapter, summarize_chapter
from notify import send_email


def parse_chapters_from_outline(outline_text: str):
    chapters = []
    for line in outline_text.splitlines():
        line = line.strip()
        if not line:
            continue

        m1 = re.match(r"^(\d+)\.\s+(.*)$", line)
        m2 = re.match(r"^chapter\s+(\d+)\s*[:\-]\s*(.*)$", line, re.IGNORECASE)

        if m1:
            chapters.append((int(m1.group(1)), m1.group(2).strip()))
        elif m2:
            chapters.append((int(m2.group(1)), m2.group(2).strip()))

    # dedupe by chapter number (keep first)
    dedup = {}
    for n, t in chapters:
        if n not in dedup:
            dedup[n] = t

    return [(n, dedup[n]) for n in sorted(dedup.keys())]


def get_previous_summaries(book_id: str, upto_chapter: int) -> str:
    resp = supabase.table("book_chapters") \
        .select("chapter_number, chapter_summary") \
        .eq("book_id", book_id) \
        .lt("chapter_number", upto_chapter) \
        .order("chapter_number") \
        .execute()

    parts = []
    for row in resp.data:
        summary = (row.get("chapter_summary") or "").strip()
        if summary:
            parts.append(f"Chapter {row['chapter_number']} summary:\n{summary}")

    return "\n\n".join(parts)


def process_chapters():
    resp = supabase.table("book_projects") \
        .select("*") \
        .eq("current_stage", "chapters") \
        .execute()

    books = resp.data

    for book in books:
        book_id = book["id"]
        title = book["title"]
        outline = (book.get("outline") or "").strip()

        if outline == "":
            print("Skipping (missing outline)")
            continue

        chapters = parse_chapters_from_outline(outline)
        print("Chapters detected from outline:", chapters)

        if not chapters:
            print("No chapters detected. Your outline must have lines like '1. Title'")
            continue

        # 1) ensure chapter rows exist
        for ch_num, ch_title in chapters:
            existing = supabase.table("book_chapters") \
                .select("id") \
                .eq("book_id", book_id) \
                .eq("chapter_number", ch_num) \
                .execute().data

            if not existing:
                supabase.table("book_chapters").insert({
                    "book_id": book_id,
                    "chapter_number": ch_num,
                    "chapter_title": ch_title,
                    "chapter_notes_status": "",
                    "chapter_notes": "",
                    "chapter_status": "pending",
                    "chapter_text": "",
                    "chapter_summary": ""
                }).execute()
                print(f"Inserted Chapter {ch_num} row")

        # 2) generate/review in order (STOP after one chapter action)
        for ch_num, ch_title in chapters:
            chapter_rows = supabase.table("book_chapters") \
                .select("*") \
                .eq("book_id", book_id) \
                .eq("chapter_number", ch_num) \
                .execute().data

            if not chapter_rows:
                print(f"ERROR: Chapter row missing for Chapter {ch_num}")
                break

            chapter = chapter_rows[0]

            chapter_text_existing = (chapter.get("chapter_text") or "").strip()
            notes_status = (chapter.get("chapter_notes_status") or "").strip().lower()
            notes = (chapter.get("chapter_notes") or "").strip()
            chapter_status = (chapter.get("chapter_status") or "").strip().lower()

            # ✅ already approved -> next
            if chapter_status == "approved":
                print(f"Chapter {ch_num} already approved, skipping")
                continue

            # ✅ if not generated yet -> generate ONCE then STOP for editor review
            if chapter_text_existing == "":
                previous_summaries = get_previous_summaries(book_id, ch_num)

                print(f"Generating Chapter {ch_num}: {ch_title}")
                new_text = generate_chapter(
                    title=title,
                    outline=outline,
                    chapter_number=ch_num,
                    chapter_title=ch_title,
                    previous_summaries=previous_summaries,
                    chapter_notes=None
                )

                new_summary = summarize_chapter(new_text)

                supabase.table("book_chapters").update({
                    "chapter_text": new_text,
                    "chapter_summary": new_summary,
                    "chapter_status": "generated",
                    "chapter_notes_status": "",   # reset
                    "chapter_notes": ""           # reset
                }).eq("id", chapter["id"]).execute()

                send_email(
                    "Chapter Ready for Review",
                    f"Chapter {ch_num} for '{title}' is generated and ready for review.\n\n"
                    f"To approve: set chapter_notes_status = no_notes_needed\n"
                    f"To regenerate: set chapter_notes_status = yes AND add chapter_notes."
                )

                print(f"Chapter {ch_num} generated → waiting review ✅")
                break

            # ✅ editor wants notes but didn't add notes -> waiting
            if notes_status == "yes" and notes == "":
                supabase.table("book_chapters").update({
                    "chapter_status": "waiting_notes"
                }).eq("id", chapter["id"]).execute()

                send_email(
                    "Waiting for Chapter Notes",
                    f"Chapter {ch_num} of '{title}' is waiting for editor notes."
                )

                print(f"Waiting for notes on Chapter {ch_num} (paused)")
                break

            # ✅ editor approved -> mark approved and continue
            if notes_status == "no_notes_needed":
                supabase.table("book_chapters").update({
                    "chapter_status": "approved"
                }).eq("id", chapter["id"]).execute()

                print(f"Chapter {ch_num} approved ✅")
                continue

            # ✅ editor gave notes -> regenerate then STOP for review again
            if notes_status == "yes" and notes != "":
                previous_summaries = get_previous_summaries(book_id, ch_num)

                print(f"Regenerating Chapter {ch_num} with notes...")
                new_text = generate_chapter(
                    title=title,
                    outline=outline,
                    chapter_number=ch_num,
                    chapter_title=ch_title,
                    previous_summaries=previous_summaries,
                    chapter_notes=notes
                )

                new_summary = summarize_chapter(new_text)

                supabase.table("book_chapters").update({
                    "chapter_text": new_text,
                    "chapter_summary": new_summary,
                    "chapter_status": "generated",
                    "chapter_notes_status": "",   # reset so editor must decide again
                    "chapter_notes": ""           # reset
                }).eq("id", chapter["id"]).execute()

                send_email(
                    "Chapter Updated for Review",
                    f"Chapter {ch_num} for '{title}' was regenerated using your notes and is ready for review."
                )

                print(f"Chapter {ch_num} regenerated → waiting review ✅")
                break

            # ✅ status blank or "no" -> pause (forces editor to choose)
            if notes_status in ["", "no"]:
                print(f"Paused: chapter_notes_status is '{notes_status or 'empty'}' for Chapter {ch_num}")
                break

        # 3) after loop: if ALL chapters approved -> move book to FINAL
        all_rows = supabase.table("book_chapters") \
            .select("chapter_status") \
            .eq("book_id", book_id) \
            .execute().data

        if all_rows and all((r.get("chapter_status") or "").lower() == "approved" for r in all_rows):
            supabase.table("book_projects").update({
                "current_stage": "final",
                "book_output_status": "ready"
            }).eq("id", book_id).execute()

            send_email(
                "All Chapters Approved",
                f"All chapters for '{title}' are approved. Book moved to FINAL stage."
            )

            print("All chapters approved → moved book to FINAL stage ✅")