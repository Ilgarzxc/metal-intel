import time
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class NotFoundError(Exception):
	pass

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
	headers = headers or {}
	headers.setdefault("User-Agent", "MyService/1.0")
	
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



