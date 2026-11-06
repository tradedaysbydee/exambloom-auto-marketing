# Activate the ExamBloom daily social publisher

**Status when first installed: SAFE PREVIEW MODE.** The workflow can run, but cannot post until the owner connects Meta and sets `PUBLISH_ENABLED=true` in GitHub repository variables.

1. On Facebook, create/administer your ExamBloom **Page** and link an Instagram **professional** account. Ordinary personal Instagram accounts are not supported by this implementation.
2. At https://developers.facebook.com/apps/ create/configure a Meta developer app with Facebook Login and the permissions required for your own Page and Instagram media publishing. Follow Meta's up-to-date instructions to obtain a valid Page access token, Page ID, and Instagram professional account ID. Some setups need Meta business verification or app review. Never put a password or token in a public file.
3. In GitHub: **Settings > Secrets and variables > Actions > Secrets**, add:
   - `META_PAGE_ACCESS_TOKEN`: the Meta Page access token
   - `META_PAGE_ID`: your Facebook Page ID (if publishing to Facebook)
   - `META_IG_USER_ID`: linked Instagram professional account ID (if publishing to Instagram)
4. Under **Variables** add `SALES_DESTINATION_URL` with your *verified* membership/sign-up URL (the homepage is used if omitted). Add `PUBLISH_ENABLED=false` for initial testing, later change it to `true`.
5. Open **Actions > ExamBloom Daily Auto Marketing > Run workflow**. In preview mode the generated artwork is not posted. After authorizing Meta, enable publishing and run again. Confirm both posts on the actual accounts.
6. The scheduler targets **18:17 Europe/London**, allowing for normal GitHub scheduling delays. The Mac can be off.
7. To pause at any time, change the repository variable `PUBLISH_ENABLED` to `false`.

Facebook links contain UTM tags. Instagram captions point to the bio link (keep the bio URL updated). To measure *paid sales*, configure your website analytics/Stripe success events separately. Organic reach and daily sales are not guaranteed.

Optional: upload your own approved campaign photography into `assets/` with filenames `family.jpg`, `test.jpg`, `challenge.jpg`. The generator uses them automatically if present; otherwise it draws purple/navy ExamBloom cards. Do not upload children's names, actual customer information, or private images without permission. 
