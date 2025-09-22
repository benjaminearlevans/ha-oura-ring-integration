OPTIMIZATION NOTES

Polling Frequency: 15-minute intervals during waking hours, 60 minutes overnight
Data Retention: Store 90 days locally for trend analysis
Cache Strategy: Cache current day data in Redis for instant access
Battery Optimization: Reduce live heart rate queries to preserve ring battery
Privacy Mode: Option to disable certain automations when guests present
Fallback Logic: Maintain last-known-good states if API unavailable