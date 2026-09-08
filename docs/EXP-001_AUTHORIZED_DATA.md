# EXP-001 authorized data boundary

Historical SPX, VIX, and SKEW observations must come from an authorized export or licensed feed. AletheiaTelos does not scrape delayed quote pages or store provider credentials.

Required ingestion provenance includes observation timestamp, availability timestamp, source identity/version, SKEW methodology version, and content hash. Revised methodology or revised history receives a new dataset identity.
