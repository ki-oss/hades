"""
This example highlights some interesting differences between hades and simpy based on their [Shared Resources example](https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html).

The key things to note are that the queue of waiting cars happens in the process rather than making use of a shared resource.

This means the state of the battery charging station contains a lot of useful information, but results in slightly less terse code and more logic within it.
"""
import asyncio

from hades import Event, Hades, NotificationResponse, PredefinedEventAdder, Process


class CarArrives(Event):
    car_id: int


class CarStartsCharging(Event):
    car_id: int


class CarLeaves(Event):
    car_id: int


class BatteryChargingStation(Process):
    def __init__(self, charging_duration: int):
        super().__init__()
        self.charging_duration = charging_duration
        self.currently_charging = set()
        self.waiting_cars = []

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case CarArrives(t=t, car_id=car_id):
                print(f"Car {car_id} arriving at {t}")
                if len(self.currently_charging) < 2:
                    self.currently_charging.add(car_id)
                    self.add_event(CarStartsCharging(t=t, car_id=car_id))
                else:
                    self.waiting_cars.append(car_id)
                return NotificationResponse.ACK
            case CarStartsCharging(t=t, car_id=car_id):
                print(f"Car {car_id} starting to charge at {t}")
                self.add_event(CarLeaves(t=t + self.charging_duration, car_id=car_id))
                return NotificationResponse.ACK
            case CarLeaves(t=t, car_id=car_id):
                print(f"Car {car_id} leaving the bcs at {t}")
                self.currently_charging.remove(car_id)
                if self.waiting_cars:
                    next_car = self.waiting_cars.pop(0)
                    self.currently_charging.add(next_car)
                    self.add_event(CarStartsCharging(t=t, car_id=next_car))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK 


async def bcs():
    hades = Hades()
    bcs = BatteryChargingStation(charging_duration=5)
    hades.register_process(bcs)

    # Creating events for cars arriving at the battery charging station
    events: list[CarArrives] = [CarArrives(t=2 * i, car_id=i) for i in range(4)]
    event_adder = PredefinedEventAdder(predefined_events=events, name="car arrivals")
    hades.register_process(event_adder)
    await hades.run()


if __name__ == "__main__":
    asyncio.run(bcs())
