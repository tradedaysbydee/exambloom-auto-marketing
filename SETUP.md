# ExamBloom automatic Instagram + TikTok marketing — free setup

## Current activation status (7 November 2026)

**LIVE PUBLISHING ENABLED.** The GitHub Actions workflow currently sets `PUBLISH_ENABLED: 'true'` directly in `.github/workflows/post-daily.yml`. The old repository variable `PUBLISH_ENABLED` no longer controls it. On the first live run, Buffer accepted one Instagram post and one TikTok post with status `sending`. Final publication must be checked in Buffer or on the platforms.

**To pause:** Open the repository **Actions** tab, select **ExamBloom Instagram and TikTok Auto Marketing**, open the **…** menu, and choose **Disable workflow**. This pauses both the daily schedule and manual runs. To resume, select **Enable workflow**. You can also edit the workflow's `PUBLISH_ENABLED` value back to `'false'` to keep preview runs working without public publication.

This version uses **Buffer**, not a Facebook Page or your own Meta/TikTok developer app. It uses the existing GitHub Actions cloud schedule, the ExamBloom graphics generator, and Buffer's current GraphQL API.

## One-time setup (you do not have to give ChatGPT your passwords)

1. Visit https://buffer.com and create a **Free** account.
2. In Buffer, connect your ExamBloom Instagram and TikTok channels. Instagram needs to be **Professional (Business or Creator)** for hands-off auto publishing; if your Instagram is Personal, switch its account type in Instagram settings. TikTok photos and videos must meet platform requirements to post automatically. Avoid features that require a mobile notification (e.g., native music/effects).
3. Visit https://publish.buffer.com/settings/api and create your Buffer API key. The page may redirect within Buffer's settings.
4. On **your GitHub repo**, open Settings > Secrets and variables > Actions > **New repository secret**. Name it `BUFFER_API_KEY` and paste the secret **there**, never in GitHub public files, a screenshot or ChatGPT.
5. On the **Variables** tab add `SALES_DESTINATION_URL` = `https://exambloom.co.uk` (or a verified direct signup/membership page), and `PUBLISH_ENABLED` = `false` for testing.
6. In the **Actions** tab, find **ExamBloom Instagram and TikTok Auto Marketing**, select **Run workflow**. This only generates a preview while `PUBLISH_ENABLED` is false. Verify a green test run.
7. When both channels are connected and you are ready to make public posts, switch `PUBLISH_ENABLED` to `true` and run the workflow again. Confirm the posts in **Buffer** and on the actual Instagram and TikTok accounts. If TikTok declines an image format, leave publishing off and check Buffer's current TikTok support.
8. The schedule targets approximately **18:17 UK time** every day; scheduled GitHub Actions may run late. Your Mac can be shut down. To stop it, set `PUBLISH_ENABLED` back to `false`.

## What this bot actually does
- Generates a new 1080×1350 branded JPEG and sales-focused caption from its built-in templates every day, with 5 benefit/membership posts and 2 quiz posts per week.
- Commits the image to your **public** repository so Buffer can retrieve it; do not put anything private in assets or generated images.
- Discovers Instagram and TikTok channels from your Buffer account and submits daily posts in **automatic** rather than reminder mode.
- Keeps a basic publication history in `data/buffer_history.json` to avoid routine duplicate submissions.

## Important conditions
- Buffer's free tier currently supports **3 connected channels and up to 10 queued posts per channel at a time**; this bot submits at most one new post per day per platform. The API is free at current limits. Third-party free limits may change.
- Buffer may reject unsupported formats or accounts. Automatic publishing is not guaranteed for content using native-only effects. **We have not tested with your real accounts yet**.
- A post accepted by Buffer is not necessarily publicly published. Check the platform or Buffer's status on first launch and periodically thereafter.
- Instagram captions do not create clickable links; add `https://exambloom.co.uk` to your Instagram bio. Set your TikTok profile link where eligible.
- To attribute **paid subscription sales**, website tracking for successful checkout completion is required separately.
- The generator is deterministic template-based (free, no paid image credits), not generative AI.
- Any credentials can expire. Reconnect your channels when Buffer asks.
