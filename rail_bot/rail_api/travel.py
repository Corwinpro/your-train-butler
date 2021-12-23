from typing import Optional


class TravelDiscruptionInfo:
    def __init__(self, event_type, event_reason, is_active):
        self.event_type = event_type
        self.event_reason = event_reason
        self.is_active = is_active

    def __repr__(self):
        return self.event_reason or f"{self.event_type}, no info."

    @classmethod
    def delay_from_departure_service(cls, departure_service):
        return cls(
            event_type="DELAY",
            event_reason=departure_service.delayReason,
            is_active=departure_service.delayReason is not None,
        )

    @classmethod
    def cancel_from_departure_service(cls, departure_service):
        is_active = False
        if departure_service.isCancelled:
            is_active = True

        return cls(
            event_type="CANCEL",
            event_reason=departure_service.cancelReason,
            is_active=is_active,
        )

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, TravelDiscruptionInfo):
            return False

        return (
            self.event_type == __o.event_type
            and self.event_reason == __o.event_reason
        )


class Travel:
    def __init__(
        self,
        origin: str,
        destination: str,
        scheduled_departure,
        service_type: str,
        delay_info: TravelDiscruptionInfo = None,
        cancel_info: TravelDiscruptionInfo = None,
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
    def is_delayed(self) -> Optional[bool]:
        if self.delay_info is None:
            return None
        return self.delay_info.is_active

    @property
    def is_cancelled(self) -> Optional[bool]:
        if self.cancel_info is None:
            return None
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
