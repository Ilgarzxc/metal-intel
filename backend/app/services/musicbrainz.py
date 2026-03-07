import asyncio
import logging
# Import functions from fetcher.py for reuse.
from .fetcher import fetch_with_retry, NotFoundError, ExternalServiceRetryFailedError


logger = logging.getLogger(__name__)

# Compile a request. Define an endpoint, format of data for return and query itself.
async def search_releases_group(tag: str, limit: int = 100, offset: int = 0):
	url = "https://musicbrainz.org/ws/2/release-group"
	params = {
		"query": tag,
		"fmt": "json",
        "limit": limit,
        "offset": offset,
	}
	# Create a client for request. Async client to avoid pending connection.
	# + Error handling
	async with httpx.AsyncClient(timeout=10.0) as client:
		try:
			response = await fetch_with_retry(client, url, params=params)
			return response.json()

		except NotFoundError:
			return {
				"error": "No releases found for this tag",
				"status": 404
			}

		except ExternalServiceRetryFailedError as exc:
			logger.error(f"MusicBrainz retry failed: {exc}")
			return {
				"error": "MusicBrainz service unavailable",
				"status": 503
			}
