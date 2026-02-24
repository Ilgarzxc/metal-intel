import httpx
import logging
from .fetcher import fetch_with_retry, NotFoundError, ExternalServiceRetryFailedError


logger = logging.getLogger(__name__)

async def search_releases_by_tag(tag: str):
	url = "https://musicbrainz.org/ws/2/release"
	params = {
		"query": f"tag:{tag}",
		"fmt": "json"
	}

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
