# ExamBloom — live organic growth bot

**Current status (7 November 2026): LIVE.** The GitHub publisher is connected to the owner's existing Buffer account and sends organic Instagram and TikTok posts. Its initial campaign has been verified as `sent` on both platforms by Buffer's read-only metrics API. No paid Meta/TikTok advertising is purchased.

## What runs automatically

**Daily content publishing** — [.github/workflows/post-daily.yml](.github/workflows/post-daily.yml)
- Creates ExamBloom-branded promotional graphics, quizzes and parent-facing copy.
- Five sales-benefit posts and two quiz posts per week, from a larger original content library.
- Tests **12:17 PM, 6:17 PM and 8:17 PM Europe/London**.
- Only the one selected scheduled run each day submits posts; other runs generate previews and exit without publishing.
- Uses real engagement data after enough comparable samples; otherwise fairly rotates options. Continues exploring new creatives/times.
- Uses `data/buffer_history.json` to prevent routine duplicate submissions.
- The `PUBLISH_ENABLED` setting is currently **hardcoded to true in the workflow**; changing an old repository variable of the same name does not disable publishing.

**Daily performance analysis** — [.github/workflows/insights.yml](.github/workflows/insights.yml)
- Collects available Buffer post metrics once per day, including views, impressions, reach and engagement where reported.
- Stores results in [PERFORMANCE.md](PERFORMANCE.md) and `data/performance.json`, with historical post IDs and creative metadata.
- Tracks progress toward **one million exposure events**, NOT one million unique people.
- Identifies better-supported themes and publishing times after adequate data. Missing metrics are not treated as zero.
- Requires the existing secret `BUFFER_API_KEY`. Buffer's metrics APIs are experimental and may change or lag the platforms.

## Pause or resume

Open the repository's **Actions** tab, select **ExamBloom Instagram and TikTok Auto Marketing**, and use the **… menu → Disable workflow** to stop new posts. Choose **Enable workflow** to resume. To keep preview functionality but disable live posts, change `PUBLISH_ENABLED: 'true'` to `PUBLISH_ENABLED: 'false'` in `.github/workflows/post-daily.yml`. The analytics workflow can remain enabled independently.

## What isn't completed yet

- **Paid-conversion attribution**: ExamBloom's live Stripe product was identified in the connected VYBE account, but the marketing repository cannot read Stripe checkout payments without a separate, secure integration. To link a particular post to a paid subscription, the ExamBloom website must preserve campaign UTM parameters and send verified checkout metadata to Stripe.
- **Ads and reach guarantee**: The bot publishes free organic posts. It does not purchase advertising, manipulate recommendation algorithms or guarantee one million impressions or customers.
- **Native short video production**: The current daily Buffer publishing route uses generated JPEG image posts. Reels/video automation needs separate compatibility testing.

See [SALES_TRACKING.md](SALES_TRACKING.md) for privacy-safe website attribution and suggested profile links.

## Support and security

Never add passwords, Buffer API keys or Stripe keys to public files. Existing Buffer authorization is in GitHub Actions secrets. GitHub Actions and Buffer are external services; schedules, access permissions and free-plan limits can change. If either social platform requires reauthorization, reconnect it inside Buffer.

Ensure profile bios point parents to `https://exambloom.co.uk`. Use parent-directed language, avoid claims of guaranteed exam performance, and handle data about children and parents appropriately under UK privacy law.
