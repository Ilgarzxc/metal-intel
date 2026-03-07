# Fetcher for resilience and reliable communication with MusicBrainz API.
# Async requests and predefined delays. Descriptive logging included.
# Retry mechanisms implemented.

import time
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

# Raised when status is 404 (Not Found)
class NotFoundError(Exception):
	pass

# Raised after all retries are exhausted
class ExternalServiceRetryFailedError(Exception):
	pass


async def fetch_with_retry(
	client: httpx.AsyncClient,
	url: str,
	params: dict | None = None,
	headers: dict | None = None,
	retries: int = 3,
	delays: list[int] = [15, 60, 900],
):
	#---Prepare headers---
	# ??? check if I have to add contact email to user-agent.
	headers = headers or {}
	headers.setdefault("User-Agent", "Metal_Albums_Fetcher (ilgar.gurbanov.90@gmail.com)")
	
	#---Retry loop---
	attempt = 0

	while attempt < retries:
		start_time = time.monotonic()

		try:
			response = await client.get(url, params=params, headers=headers)
			duration_ms = int((time.monotonic() - start_time) * 1000)

			# ---Success---
			if response.status_code == 200:
				logger.info(
					"[Success]\n"
					"{\n"
					f' "status": {response.status_code},\n'
					f' "url": "{url}",\n'
					f' "params": {params},\n'
					f' "duration_ms": {duration_ms}\n'
					"}"
				)
				return response

			# ---Not Found---
			if response.status_code == 404:
				raise NotFoundError(f"Resource not found at {url}")

			# ---Retryable statuses---
			if response.status_code >= 500 or response.status_code in (429,):
				if attempt < retries:
					delay = delays[min(attempt, len(delays) - 1)]
					logger.warning(
						f"[Retry {attempt + 1} of {retries}]\n"
						"{\n"
						f' "status": {response.status_code},\n'
						f' "url": "{url}",\n'
						f' "params": {params},\n'
						f' "duration_ms": {duration_ms},\n'
						f' "next_delay": {delay}\n'
						"}"
					)
					await asyncio.sleep(delay)
					attempt += 1
					continue

				# No retries left -> Final failure
				break

			# --- Non-retryable error ---
			raise ExternalServiceRetryFailedError(
				f"Unexpected status {response.status_code} from external service"
			)
		# Raise in case of network / connectivity issues.
		except (httpx.ConnectError, httpx.ReadTimeout, httpx.NetworkError) as e:
			duration_ms = int((time.monotonic() - start_time) * 1000)

			if attempt < retries:
				delay = delays[min(attempt, len(delays) - 1)]
				logger.warning(
					f"[Retry {attempt + 1} of {retries}]\n"
					"{\n"
					f' "exception": "{type(e).__name__}",\n'
					f' "url": "{url}",\n'
					f' "duration_ms": {duration_ms}\n'
					f' "next_delay": {delay}\n'
					"}"
				)
				await asyncio.sleep(delay)
				attempt += 1
				continue

	# ---Final failure log---
	logger.error(
		"[Retry failed]\n"
		"{\n"
		f' "retries": {retries},\n'
		f' "last_status": {response.status_code if "response" in locals() else None},\n'
		f' "url": "{url}",\n'
		f' "params": {params},\n'
		f' "message": "External service did not respond successfully after {retries} retries"\n'
		"}"
	)

	raise ExternalServiceRetryFailedError(
		f"External service did not respond successfully after {retries} retries"
	)



