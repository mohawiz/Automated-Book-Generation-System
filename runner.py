from outline_stage import process_outlines
from chapter_stage import process_chapters
from final_stage import compile_book

if __name__ == "__main__":
    process_outlines()
    process_chapters()
    compile_book()