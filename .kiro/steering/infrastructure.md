# Infrastructure

## When to Apply
When discussing deploy, CI/CD, or AWS resources.

## Rules
- Hosted on S3 behind CloudFront
- Region: us-east-1
- Deploy via GitHub Actions — never manual S3 sync
- Budget alarm at $10/month — always keep costs minimal
- This dashboard aggregates data from all chapter sites
- Chapters: Brazil, Poland, UK, Chile (active), USA, France (onboarding)
