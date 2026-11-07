# ExamBloom paid-sales attribution (not yet connected to the website)

## What is working
- Daily Instagram and TikTok publishing via Buffer.
- Daily per-post impressions, views, reach, likes, comments, shares where Buffer provides them.
- Controlled creative and posting-time experiments.
- Campaign progress toward one million **exposure events**, NOT deduplicated people.
- All reports include real recorded values only.

## What still needs website access
The bot cannot prove purchases came from posts until **exambloom.co.uk** saves campaign UTM parameters during signup/checkout and attaches them to a paid order or subscription, or until a consent-aware analytics integration records a successful checkout attributed to the campaign.

Use one tracked profile link per platform:
- Instagram: `https://exambloom.co.uk/?utm_source=instagram&utm_medium=organic_social&utm_campaign=exambloom_growth`
- TikTok: `https://exambloom.co.uk/?utm_source=tiktok&utm_medium=organic_social&utm_campaign=exambloom_growth`

Add the right link to each account's bio or profile website field, where eligible. These URLs are ordinary website links; they do **not** create an attribution system by themselves.

## A safe implementation for the website
1. In the website signup/checkout flow, preserve source, medium, campaign and content from the first visit, consistent with your privacy and consent policies.
2. When the parent starts a subscription, attach a limited campaign ID to Stripe Checkout Session / Subscription `metadata`; do not attach the child's personal details.
3. On the server, use verified Stripe webhooks (`invoice.paid` and subscription events) to count **completed paid subscription invoices**, and use `checkout.session.completed` only for signups/checkout records, not proof of paid recurring invoices.
4. Keep payment transaction IDs and customer information **out of this public GitHub repository**. Use a secure private reporting store. Only expose anonymous aggregate counts in a public dashboard if you intentionally approve their publication.
5. Match campaign metadata to aggregated invoice payments to calculate conversion rate and revenue per campaign. Attribution is limited when visitors switch devices, block analytics or visit directly later.
6. Record refunds, discounts, VAT/tax and processing fees separately before reporting net revenue or ROAS.

We have located the live Stripe product for ExamBloom Family Membership in the VYBE account, but the marketing GitHub bot does not have Stripe access or checkout metadata. Do not add full Stripe secret keys to the repository; use a restricted secret or an established server-side integration only if you want an independent payment collector.

**Important:** No automatic paid customer attribution is claimed until this website connection is completed and tested.

## Marketing measurement guardrails
- Buffer analytics may lag by around 24 hours and different platforms report different metrics.
- One million *summed* post views or impressions does not mean one million unique people.
- A good engagement score is a proxy for interest, not evidence of subscriber purchases.
- Always target UK parents/guardians, not minors, with promotional calls to action.
- Avoid manufactured engagement, guaranteed exam results and invented testimonials.
