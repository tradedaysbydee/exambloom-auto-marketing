# Approved ExamBloom advert gallery

This directory is wired into the **live Instagram and TikTok GitHub Actions publisher**.

Upload these eight JPG files here, retaining their exact filenames:

| Filename | Campaign |
|---|---|
| `01_create_tests.jpg` | Create a test in seconds |
| `02_family_learning_together.jpg` | Family celebrating progress |
| `03_guided_lessons.jpg` | Guided lessons and learning journey |
| `04_family_learning_at_home.jpg` | Family using quiz and progress features |
| `05_daily_brain_sprint.jpg` | Daily Brain Sprint and points leaderboard |
| `06_parent_child_practice.jpg` | Parent and child practising together |
| `07_progress_and_badges.jpg` | Progress charts, achievement badges and reports |
| `08_family_celebrates_progress.jpg` | Family celebrating a quiz result |

The captions and rotation order are defined in [manifest.json](manifest.json).

## One-time upload from your Mac
1. Download `ExamBloom_8_Ads_GitHub_Upload.zip` from ChatGPT.
2. Double-click the ZIP in Finder. Open `assets/campaigns` inside the extracted folder.
3. In this directory on GitHub, click **Add file → Upload files**.
4. Drag in **all eight JPG images**, not the ZIP itself.
5. Click **Commit changes** to save to `main`.

Once all eight images are present, the existing daily workflow automatically selects one on **Monday, Tuesday, Thursday and Friday**. Other days keep the current quiz/standard promotion. All eight rotate across two weeks of gallery slots; then the rotation repeats.

### Important
- Uploading files to this public repository makes the advert images public.
- Only the currently selected day's graphic gets sent to Buffer, not all eight at once.
- If a file is missing, the live bot falls back to its existing branded template, without failing.
- To pause future publication, disable the **ExamBloom Instagram and TikTok Auto Marketing** workflow in Actions.
- Photos used in ads should be approved for public use. Review any on-screen learner names or results before uploading.
