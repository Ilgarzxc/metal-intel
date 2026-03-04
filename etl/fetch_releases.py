'''
ETL - extract / transform / load
MVP: MUSICBRAINZ SERVICE STRATEGY & ROADMAP
(AI-generated)
1. DATA SCOPE (Release Groups):
   - Primary target: 'release-groups' to avoid duplicate entries for various 
     reissue formats (CD, Vinyl, Digital).
   - Filtering: Focus on 'primary-type': 'Album' to exclude singles and EPs.

2. FETCHING STRATEGY (Pagination & Resilience):
   - Offset-based pagination: MB limits response size, so we must loop through 
     results using 'offset' and 'count'.
   - Rate Limiting: Strict 1 request/sec policy. Leverages fetcher's 
     asyncio.sleep to prevent IP bans.
   - Sequential processing: Each page request waits for the previous one 
     to complete (ensure clean async flow).

3. TRANSFORMATION & CLEANING:
   - Schema Mapping: Convert MB JSON fields to internal 'ReleaseCreate' Pydantic models.
   - Tag Validation: Filter 'tags' list to extract legitimate genres while 
     discarding non-musical metadata (e.g., 'rock' if it's too generic, or user tags).

4. FUTURE IMPROVEMENTS:
   - Duplicate Prevention: Implement a lookup check before inserting to DB.
   - Monthly Sync: Integration with scheduler.py for automated library updates.
   - Metadata Enrichment: Potentially fetching labels and countries from 
     linked 'releases' inside the group.
'''