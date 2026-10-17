
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Cologne Tram API",
    description="A Simple API for the KVB-Trams in Cologne. Pretty much a learning project by me to learn python and APIs",
    version="0.1.2",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
r = httpx.get("https://www.kvb.koeln/generated/?aktion=show&code=24", headers=HEADERS, follow_redirects=True)
with open("debug.html", "w", encoding="iso-8859-1") as f:
    f.write(r.content.decode("iso-8859-1"))


KVBTram_QR_URL = "https://www.kvb.koeln/generated/?aktion=show&code={station_id}"


class Departure(BaseModel):
    line: str
    destination: str
    minutes: int | None # The KVB uses Now to express that a train is now arriving thus no minute display

class DepartureResponse(BaseModel):
    station_id: int
    station_name: str
    departures:list[Departure]
    fetched_at: datetime

class Stop(BaseModel):
    station_id: int
    station_name: str

async def fetch_departures(station_id: int) -> str:
    url= KVBTram_QR_URL.format(station_id=station_id)
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = response.content.decode("iso-8859-1")
            return text
    except Exception as err:
        raise HTTPException(status_code=502, detail=str(err))



# Parsing the departures
# Parsing the KVB QR page into a structure
# (Line, Dest, Minutes)
def parse_departures(html: str) -> tuple[str | None, list[Departure]]:
    soup = BeautifulSoup(html, "html.parser")

    h1 =soup.find("h2")
    station_name = h1.get_text(strip=True) if h1 else ""


    departures: list[Departure] = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        line = cells[0].get_text(strip=True)
        destination = cells[1].get_text(strip=True)
        minutes_text = cells[2].get_text(strip=True)

        if not line.isdigit():
            continue

        if minutes_text == "Sofort":
            minutes = None
        elif minutes_text.endswith("Min"):
            minutes = int(minutes_text.split()[0])
        else:
            continue
        departures.append(Departure(line=line, destination=destination, minutes=minutes))
    return station_name, departures

@app.get("/", tags=["meta"])
async def root():
    return {"service": "KVB Tram Departures API",
            "docs": "/docs",
            "example": "/departures/24"} #Should be Zülpi :D (Zülpicher Platz)


@app.get("/departures/{station_id}", response_model=DepartureResponse, tags=["departures"])
async def departures(
        station_id: int,
        limit: int = Query(10, ge=1, le=20, description="Limit the number of departures to return"),
):
    #Live Departs for a Stop, eg GET /departures/24?limit=5
    html = await fetch_departures(station_id)
    station_name, pdepartures = parse_departures(html)
    if not pdepartures:
        raise HTTPException(status_code=404, detail="No departures found")
    return DepartureResponse(
        station_id=station_id,
        station_name=station_name,
        fetched_at=datetime.now(),
        departures= pdepartures[:limit],
    )

@app.get("/stops", tags=["stops"])
async def list_stops(q: str | None = Query(None, description="Search stops by station name")):
    stops = None
    if q:
        stops = [s for s in stops if q.lower() in s.name.lower()]
    return {"stops": stops}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)