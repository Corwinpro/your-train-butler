import os

from zeep import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin

WATERBEACH_CODE = "EUS" # LST
CAMBRIDGE_CODE = "BHI" # CBG

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


class TravelDiscruptionInfo:
    def __init__(self, event_type, event_reason):
        self.event_type = event_type
        self.event_reason = event_reason

    def __repr__(self):
        return self.event_reason or f"{self.event_type}, no info."

    @property
    def is_active(self):
        return self.event_reason is not None

    @classmethod
    def delay_from_departure_service(cls, departure_service):
        return cls(
            event_type="DELAY",
            event_reason=departure_service.delayReason,
        )

    @classmethod
    def cancel_from_departure_service(cls, departure_service):
        return cls(
            event_type="CANCEL",
            event_reason=departure_service.cancelReason,
        )


class Travel:
    def __init__(
        self,
        origin,
        destination,
        scheduled_departure,
        service_type,
        delay_info: TravelDiscruptionInfo=None,
        cancel_info: TravelDiscruptionInfo=None,
        scheduled_arrival=None,
        estimated_arrival=None,
        estimated_departure=None,
    ) -> None:
        self.origin = origin
        self.destination = destination

        self.service_type = service_type

        self.scheduled_departure = scheduled_departure
        self.estimated_departure = estimated_departure

        self.scheduled_arrival = scheduled_arrival
        self.estimated_arrival = estimated_arrival

        self.delay_info = delay_info
        self.cancel_info = cancel_info

    def __repr__(self) -> str:
        repr = (
            f"Travel info:\n{self.service_type.title()} "
            f"{self.origin} - {self.destination}\n"
            f"Scheduled at {self.scheduled_departure} "
            f"(expected {self.estimated_departure or 'unknown'})\n"
        )
        if self.is_delayed:
            repr = f"WARNING: {self.delay_info!r}\n" + repr

        if self.is_cancelled:
            repr = f"WARNING: {self.cancel_info!r}\n" + repr

        return repr

    @property
    def is_delayed(self):
        return self.delay_info.is_active or (
            self.estimated_departure is not None
            and self.scheduled_departure is not None
            and self.estimated_departure != self.scheduled_departure
        )

    @property
    def is_cancelled(self):
        return self.cancel_info.is_active

    @classmethod
    def from_departure_service(cls, departure_service):
        return cls(
            origin=departure_service.origin.location[0].locationName,
            destination=departure_service.destination.location[0].locationName,
            scheduled_departure=departure_service.std,
            service_type=departure_service.serviceType,
            delay_info=TravelDiscruptionInfo.delay_from_departure_service(
                departure_service
            ),
            cancel_info=TravelDiscruptionInfo.cancel_from_departure_service(
                departure_service
            ),
            scheduled_arrival=departure_service.sta,
            estimated_arrival=departure_service.eta,
            estimated_departure=departure_service.etd,
        )


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
        msg += f"{service.std} to {destination} - {service.etd}\n"

    return msg


def next_departure_status(from_station: str, to_station: str, timeOffset=0):
    res = client.service.GetNextDepartures(
        crs=from_station.upper(),
        filterList=[to_station.upper()],
        timeOffset=timeOffset,
        _soapheaders=[header_value],
    )
    departure_service = res.departures.destination[0].service
    travel = Travel.from_departure_service(departure_service)
    return travel
