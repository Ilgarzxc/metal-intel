import httpx
import asyncio

async def fetch_sample_data():
    url = "https://musicbrainz.org/ws/2/release-group"
    headers = {"User-Agent": "Metal_Albums_Fetcher (ilgar.gurbanov.90@gmail.com)"}
    params = {
        "query": "artist:Manowar AND primarytype:Album",
        "fmt": "json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        return data.get("release-groups", [])
    

async def main():
    groups = await fetch_sample_data()

    if groups:
        print(f"Found albums: {len(groups)}")
        print("First element of the list:")
        for k, v in groups[0].items():
            if k == "title":
                print(v)
    else:
        print("Nothing found")

if __name__ == "__main__":
    asyncio.run(main())