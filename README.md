📘 AI Book Generation Pipeline (Supabase + Python)

This project is an AI-powered book generation system.
It generates a book step by step with human-in-the-loop review using Supabase as the database.

The flow is:

Generate outline

Approve outline

Generate chapters one by one

Editor reviews each chapter

Approve or regenerate chapters using notes

Compile final book (DOCX)

🧱 Tech Stack

Python

Supabase (Postgres database)

LLM API (for outline & chapter generation)

SMTP Email (notifications)

📂 Project Structure
MediaMarson/
│
├── runner.py                # Main entry point
├── outline_stage.py         # Outline generation logic
├── chapter_stage.py         # Chapter generation & review logic
├── final_stage.py           # Final book compilation
├── notify.py                # Email notifications (SMTP)
├── db.py                    # Supabase connection
├── llm.py                   # LLM helper functions
├── .env                     # Environment variables
⚙️ Environment Setup
1️⃣ Create .env file
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_service_key


SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=receiver_email@gmail.com

⚠️ Use Gmail App Password, not your real password.

▶️ How to Run the System

Always run from the project root:

python runner.py

runner.py runs all stages in order:

outline_stage

chapter_stage

final_stage

🧠 Outline Stage (outline_stage.py)
What it does

Generates an outline using AI

Saves it in book_projects.outline

Waits for editor approval

Requirements to generate outline

In book_projects table:

notes_on_outline_before → must be filled

outline → must be empty

After generation

outline_status = generated

current_stage = outline

👉 You must manually approve the outline before chapters start.

✅ How to Approve Outline

In Supabase → book_projects table:

Set:

outline_status = approved
current_stage = chapters

Then run:

python runner.py
✍️ Chapter Stage (chapter_stage.py)
What it does

Reads outline

Creates chapter rows

Generates one chapter at a time

Stops after each chapter for editor review

Uses previous chapter summaries as context

📌 Chapter Review Logic (IMPORTANT)

Each chapter has these key columns:

chapter_text

chapter_summary

chapter_notes_status

chapter_notes

chapter_status

✅ How to Approve a Chapter

In book_chapters table:

For the chapter you want to approve:

chapter_notes_status = no_notes_needed

Do NOT manually change chapter_status.

Then run:

python runner.py

➡️ Next chapter will be generated.

🔁 How to Regenerate a Chapter (With Notes)

If the chapter needs changes:

chapter_notes_status = yes
chapter_notes = "Make it simpler and add examples"

Then run:

python runner.py

Result:

Chapter regenerated

Email sent

Script stops again for review

⏸️ Why the Script Stops Often (This Is Correct)

The system is designed to stop after:

generating a chapter

regenerating a chapter

waiting for notes

This ensures:

no chapters are auto-approved

editor always stays in control

📧 Email Notifications Sent

Emails are automatically sent for:

✅ Chapter Ready for Review

✅ Waiting for Editor Notes

✅ Chapter Updated for Review

✅ All Chapters Approved

(Outline-ready email can be added easily.)

🏁 Final Stage

When all chapters are approved:

current_stage → final

Book is compiled into DOCX

Email sent: All Chapters Approved

🧪 Testing Checklist

Add a row in book_projects

Fill notes_on_outline_before

Run python runner.py

Approve outline

Run again

Approve/regenerate chapters one by one

Final DOCX generated 🎉

📌 Notes

Approval is manual by design

Supabase is the “editor UI”

Safe for academic or production demos

