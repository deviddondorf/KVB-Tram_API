# KVB Tram Station API
This learning project is a FastAPI that looks for upcoming trams on Station X.<br>
It is a very simple API wrapped around a scraper I build utilising the BeautifulSoup parser as I ran into issues using Regex.<br>

The API is „compact“ as it owns no own data and every request is handled by the KVB website.<br>
It handles pretty much error and serves the departure data as a JSON.

## Requirements
fastapi <br>
uvicorn <br>
httpx <br>
pydantic <br>
beautifulsoup4 <br>

## License
This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.<br>
Copyright (c) 2026 Devid Dondorf
