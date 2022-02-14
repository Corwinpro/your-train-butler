import datetime
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union

from rail_bot.utils import format_time, parse_time

logger = logging.getLogger(__name__)


# Standard estimated departure time label string as returned by the LDB service
ON_TIME_LABEL = "On time"
# Estimated departure time label string as returned by the LDB service
# for a cancelled service
CANCELLED_LABEL = "Cancelled"


TD = TypeVar("TD", bound="TravelDisruptionInfo")


class TravelDisruptionInfo:
    def __init__(self, event_type, event_reason, is_active):
        self.event_type = event_type
        self.event_reason = event_reason
        self.is_active = is_active

    def __repr__(self):
        return self.event_reason or f"{self.event_type}, no info."

    @classmethod
    def delay_from_response_service(cls: Type[TD], service: Dict) -> TD:
        return cls(
            event_type="DELAY",
            event_reason=service["delayReason"],
            is_active=service["delayReason"] is not None,
        )

    @classmethod
    def cancel_from_response_service(cls: Type[TD], service: Dict) -> TD:
        is_active = False
        if "isCancelled" in service:
            is_active = True

        return cls(
            event_type="CANCEL",
            event_reason=service["cancelReason"],
            is_active=service["cancelReason"] is not None,
        )

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, TravelDisruptionInfo):
            return False

        return (
            self.event_type == __o.event_type and self.event_reason == __o.event_reason
        )


T = TypeVar("T", bound="Travel")


class Travel:
    def __init__(
        self,
        origin: str,
        destination: str,
        scheduled_departure: datetime.time,
        estimated_departure: Union[datetime.time, str],
        scheduled_arrival: datetime.time,
        estimated_arrival: Union[datetime.time, str],
        service_type: str,
        delay_info: Optional[TravelDisruptionInfo] = None,
        cancel_info: Optional[TravelDisruptionInfo] = None,
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
        repr = f"{self.service_type.title()} {self.origin} - {self.destination}"
        if self.is_cancelled:
            repr = f"CANCELLED: {self.cancel_info!r}\n" + repr
            return repr
        if self.is_delayed:
            repr = f"DELAYED: {self.delay_info!r}\n" + repr

        repr += f"\nScheduled at {format_time(self.scheduled_departure)}"
        if self.estimated_departure != self.scheduled_departure:
            repr += f" (expected {format_time(self.estimated_departure) or 'unknown'})"

        return repr

    @property
    def is_delayed(self) -> Optional[bool]:
        if self.delay_info is None:
            return None
        return (
            self.delay_info.is_active
            and self.scheduled_departure != self.estimated_departure
        )

    @property
    def is_cancelled(self) -> Optional[bool]:
        if self.cancel_info is None:
            return None
        return (
            self.cancel_info.is_active
            and self.scheduled_departure != self.estimated_departure
        )

    @classmethod
    def from_response(cls: Type[T], response: Dict[str, Any]) -> T:
        origin_location_name = response["locationName"]

        destination_data = response["departures"]["destination"][0]
        destination_service = destination_data["service"]
        destination_location_crs = destination_data["crs"]

        scheduled_departure = parse_time(destination_service["std"])
        if destination_service["etd"] == ON_TIME_LABEL:
            estimated_departure = scheduled_departure
        elif destination_service["etd"] == CANCELLED_LABEL:
            estimated_departure = destination_service["etd"]
        else:
            try:
                estimated_departure = parse_time(destination_service["etd"])
            except Exception as e:
                logger.warning(f"Could not parse `estimated_departure` time: {e}")
                estimated_departure = destination_service["etd"]

        calling_points = destination_service["subsequentCallingPoints"][
            "callingPointList"
        ][0]["callingPoint"]
        (destination_calling_point,) = [
            point
            for point in calling_points
            if point["crs"] == destination_location_crs
        ]

        destination_location_name = destination_calling_point["locationName"]
        scheduled_arrival = parse_time(destination_calling_point["st"])
        estimated_arrival = destination_calling_point["et"]
        if destination_calling_point["et"] == ON_TIME_LABEL:
            estimated_arrival = scheduled_arrival
        else:
            try:
                estimated_arrival = parse_time(destination_calling_point["et"])
            except Exception as e:
                logger.warning(f"Could not parse `estimated_arrival` time: {e}")
                estimated_arrival = destination_calling_point["et"]

        return cls(
            origin=origin_location_name,
            destination=destination_location_name,
            scheduled_departure=scheduled_departure,
            estimated_departure=estimated_departure,
            scheduled_arrival=scheduled_arrival,
            estimated_arrival=estimated_arrival,
            service_type=destination_service["serviceType"],
            delay_info=TravelDisruptionInfo.delay_from_response_service(
                destination_service
            ),
            cancel_info=TravelDisruptionInfo.cancel_from_response_service(
                destination_service
            ),
        )

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Travel):
            return False

        compare_attributes = [
            "origin",
            "destination",
            "scheduled_departure",
            "service_type",
            "delay_info",
            "cancel_info",
            "scheduled_arrival",
            "estimated_arrival",
            "estimated_departure",
            "is_delayed",
            "is_cancelled",
        ]
        all_equal = all(
            getattr(self, attr) == getattr(__o, attr) for attr in compare_attributes
        )
        return all_equal
