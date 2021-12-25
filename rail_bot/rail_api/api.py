import os
from typing import Optional

from zeep.client import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin

from rail_bot.rail_api.travel import Travel


LDB_TOKEN = os.environ.get("LDB_TOKEN", "")
WSDL = "http://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx?ver=2017-10-01"

client = Client(wsdl=WSDL, plugins=[HistoryPlugin()])

header = xsd.Element(
    "{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken",
    xsd.ComplexType(
        [
            xsd.Element(
                "{http://thalesgroup.com/RTTI/2013-11-28/Token/types}TokenValue",
                xsd.String(),
            ),
        ]
    ),
)
header_value = header(TokenValue=LDB_TOKEN)


def departure_board(from_station: str, to_station, rows=None):
    from_station = from_station.upper()

    if to_station is not None:
        to_station = to_station.upper()

    if rows is not None:
        rows = int(rows)
    else:
        rows = 10

    try:
        res = client.service.GetDepBoardWithDetails(
            numRows=rows,
            crs=from_station,
            filterCrs=to_station,
            _soapheaders=[header_value],
        )
    except Exception as e:
        return (
            f"Something bad just happened... Check if the input to the"
            f" departure board command is correct."
            f"(Details: {e!r}."
        )

    if res.trainServices is None:
        return (
            f"Could not retrieve board information for trains from "
            f"{from_station!r} to {to_station!r}. "
            "Are the station codes correct?"
        )

    msg = f"Trains at {res.locationName}\n"
    for service in res.trainServices.service:
        destination = service.destination.location[0].locationName
        msg += f"{service.std} to {destination} - {service.etd}"

        if service.platform is not None:
            msg += f" (Platform {service.platform})"

        msg += "\n"

    return msg


def next_departure_status(
    from_station: str, to_station: str, timeOffset: int = 0
) -> Optional[Travel]:
    res = client.service.GetNextDepartures(
        crs=from_station.upper(),
        filterList=[to_station.upper()],
        timeOffset=timeOffset,
        _soapheaders=[header_value],
    )
    departure_service = res.departures.destination[0].service
    try:
        travel = Travel.from_departure_service(departure_service)
    except AttributeError:
        travel = None
    return travel
