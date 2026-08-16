# AcmeCRM Setup Guide

## 1. Create your account
Sign up at acmecrm.com with your work email. You can start with a 14-day free trial, no credit card required.

## 2. Import contacts
From the dashboard, go to Settings -> Data -> Import and upload a CSV with your contacts. Required columns are `name` and `email`. Optional columns include `company`, `phone`, and `owner`.

## 3. Configure your pipeline
Go to Deals -> Pipeline Settings. The default pipeline has four stages: New, Contacted, Qualified, and Won. You can rename stages, reorder them, or add custom stages.

## 4. Connect email
Go to Settings -> Email -> Connect. Use Google or Microsoft OAuth, or add an IMAP/SMTP connection. Enable email tracking so opens and clicks are logged on each contact's timeline.

## 5. Set up integrations
AcmeCRM integrates with Zapier, Slack, HubSpot Marketing, and QuickBooks. Find all integrations under Settings -> Integrations.

## 6. Invite your team
Settings -> Team -> Invite Member. Assign roles: admins manage billing and team access; managers see all pipelines; members only see deals assigned to them.

## 7. Go live
When you are ready, switch from trial to a paid plan under Settings -> Billing. Your trial data is preserved, nothing resets.

## Troubleshooting
- Emails not syncing? Re-authorize the email connection under Settings -> Email.
- Imports failing? Make sure your CSV has a `name` column and is under 10 MB.
- Integrations not triggering? Verify the integration is active and test with a live webhook payload.
