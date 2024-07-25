# Copyright 2023 Brit Group Services Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import logging
import sys
from typing import Union

from pydantic import BaseModel, ConfigDict

from hades import Event, Hades, NotificationResponse, PredefinedEventAdder, Process
from hades.visualisation.websockets import HadesWS

_logger = logging.getLogger(__name__)


class WormPopsHisHeadUp(Event):
    worm_id: int
    worm_position: tuple[int, int]


class WormHid(Event):
    worm_id: int


class WormEaten(Event):
    worm_id: int
    boid_id: int


class BoidMovement(BaseModel):
    position: tuple[int, int]
    velocity: tuple[float, float]

    def distance(self, other: Union["BoidMovement", tuple[int, int]]) -> float:
        if isinstance(other, BoidMovement):
            ox, oy = other.position
        else:
            ox, oy = other
        dx = self.position[0] - ox
        dy = self.position[1] - oy
        return (dx**2 + dy**2) ** (1 / 2)

    @property
    def speed(self) -> float:
        return (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** (1 / 2)

    def move(self, grid_size: tuple[int, int]):
        x, y = self.position
        vx, vy = self.velocity
        self.position = (int(x + vx) % grid_size[0], int(y + vy) % grid_size[1])


class ImmutableMovement(BoidMovement):
    model_config = ConfigDict(frozen=True)


class BoidMoved(Event):
    boid_id: int
    movement: ImmutableMovement


class WormHider(Process):
    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case WormPopsHisHeadUp(t=t, worm_id=worm_id):
                self.add_event(WormHid(t=t + 100, worm_id=worm_id))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class Boid(Process):
    def __init__(self, boid_identifier: int, grid_size: tuple[int, int]) -> None:
        self._grid_size = grid_size
        self._boid_identifier = boid_identifier
        self._movement: BoidMovement | None = None
        self._other_boid_positions: dict[int, BoidMovement] = {}

        self._visual_range = 100
        self._worm_eat_distance = 8

        self._target_worm: tuple[int, tuple[int, int]] | None = None

        super().__init__()

    @property
    def instance_identifier(self):
        return self._boid_identifier

    def _ensure_seperation(self):
        """separation: steer to avoid crowding local flockmates"""
        if not self._movement:
            return
        seperation_factor = 0.05
        min_distance = 20
        move_x, move_y = 0, 0
        for other_boid_id, other_boid_position in self._other_boid_positions.items():
            if other_boid_id != self._boid_identifier:
                if self._movement.distance(other_boid_position) < min_distance:
                    move_x += self._movement.position[0] - other_boid_position.position[0]
                    move_y += self._movement.position[1] - other_boid_position.position[1]
        self._movement.velocity = (
            self._movement.velocity[0] + (move_x * seperation_factor),
            self._movement.velocity[1] + (move_y * seperation_factor),
        )

    def _align(self):
        """alignment: steer towards the average heading of local flockmates"""
        if not self._movement:
            return
        align_factor = 0.02
        average_vx, average_vy, num_neighbours = 0, 0, 0
        for other_boid in self._other_boid_positions.values():
            if self._movement.distance(other_boid) < self._visual_range:
                average_vx += other_boid.velocity[0]
                average_vy += other_boid.velocity[1]
                num_neighbours += 1
        try:
            self._movement.velocity = (
                self._movement.velocity[0]
                + ((average_vx / num_neighbours) - self._movement.velocity[0]) * align_factor,
                self._movement.velocity[1]
                + ((average_vy / num_neighbours) - self._movement.velocity[1]) * align_factor,
            )
        except ZeroDivisionError:
            return

    def _cohere(self):
        """cohesion: steer to move towards the average position (center of mass) of local flockmates"""
        if not self._movement:
            return
        coherence_factor = 0.002
        average_x, average_y = self._movement.position
        count_near = 0
        for movement in self._other_boid_positions.values():
            if self._movement.distance(movement) < self._visual_range:
                average_x += movement.position[0]
                average_y += movement.position[1]
                count_near += 1
        if count_near == 0:
            return
        center_x = average_x / count_near
        center_y = average_y / count_near
        self._movement.velocity = (
            self._movement.velocity[0] + (center_x - self._movement.position[0]) * coherence_factor,
            self._movement.velocity[1] + (center_y - self._movement.position[1]) * coherence_factor,
        )

    def _move_to_target_worm(self):
        if not self._movement or not self._target_worm:
            return
        worm_attraction = 0.01

        _, (worm_x, worm_y) = self._target_worm

        self._movement.velocity = (
            self._movement.velocity[0] + (worm_x - self._movement.position[0]) * worm_attraction,
            self._movement.velocity[1] + (worm_y - self._movement.position[1]) * worm_attraction,
        )

    def _keep_within_bounds(self):
        if not self._movement:
            return
        margin = self._grid_size[0] // 5
        turnFactor = 2

        velocity_x = self._movement.velocity[0]
        velocity_y = self._movement.velocity[1]

        if self._movement.position[0] < margin:
            velocity_x += turnFactor

        if self._movement.position[0] > self._grid_size[0] - margin:
            velocity_x -= turnFactor

        if self._movement.position[1] < margin:
            velocity_y += turnFactor

        if self._movement.position[1] > self._grid_size[1] - margin:
            velocity_y -= turnFactor

        self._movement.velocity = (velocity_x, velocity_y)

    def _slow_down(self):
        if not self._movement:
            return
        vx, vy = self._movement.velocity
        speed = self._movement.speed
        max_speed = 10
        if speed < max_speed:
            return

        self._movement.velocity = (max_speed * (vx / speed), max_speed * (vy / speed))

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case BoidMoved(t=t, boid_id=boid_id, movement=movement):
                self._other_boid_positions[boid_id] = movement
                if boid_id == self._boid_identifier:
                    # We will only get this once per time step so its our opportunity to move!
                    if not self._movement:
                        self._movement = BoidMovement(**movement.dict())
                    self._move_to_target_worm()
                    self._cohere()
                    self._ensure_seperation()
                    self._align()
                    self._slow_down()
                    self._movement.move(grid_size=self._grid_size)
                    if self._target_worm:
                        worm_id, worm_position = self._target_worm
                        if self._movement.distance(worm_position) < self._worm_eat_distance:
                            _logger.info(f"worm {worm_id} eaten by boid {self._boid_identifier}")
                            self.add_event(
                                WormEaten(
                                    t=t + 1,
                                    worm_id=worm_id,
                                    boid_id=self._boid_identifier,
                                )
                            )
                    self.add_event(
                        BoidMoved(t=t + 1, boid_id=boid_id, movement=ImmutableMovement(**self._movement.dict()))
                    )
                return NotificationResponse.ACK
            case WormPopsHisHeadUp(t=t, worm_position=position, worm_id=worm_id):
                if self._movement and self._movement.distance(position) < self._visual_range * 2:
                    _logger.info(f"worm {worm_id} being targeted by {self._boid_identifier}")
                    self._target_worm = (worm_id, position)
                return NotificationResponse.ACK
            case WormEaten(worm_id=worm_id) | WormHid(worm_id=worm_id):
                if self._target_worm and self._target_worm[0] == worm_id:
                    self._target_worm = None
                    return NotificationResponse.ACK
                return NotificationResponse.ACK_BUT_IGNORED
        return NotificationResponse.NO_ACK


class BoidMovementHistory(Process):
    def __init__(
        self,
        grid_size: tuple[int, int],
        current_t: int = 0,
    ) -> None:
        self._grid_size = grid_size
        self._boid_history = [[]]
        self._worms_alive = {}
        self._worm_history = [[]]
        self._fed_boids = set()
        self._current_t = current_t
        super().__init__()

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case BoidMoved(t=t, boid_id=boid_id, movement=movement):
                if t != self._current_t:
                    self._worm_history.append(list(self._worms_alive.values()))
                    self._boid_history.append([])
                    self._current_t = t
                self._boid_history[-1].append({
                    "boid_id": boid_id,
                    "movement": movement.dict(),
                    "full": boid_id in self._fed_boids,
                })

                return NotificationResponse.ACK
            case WormPopsHisHeadUp(t=t, worm_position=position, worm_id=worm_id):
                self._worms_alive[worm_id] = position
                return NotificationResponse.ACK

            case WormEaten(worm_id=worm_id) | WormHid(worm_id=worm_id) as event:
                if isinstance(event, WormEaten):
                    self._fed_boids.add(event.boid_id)
                try:
                    del self._worms_alive[worm_id]
                except KeyError:
                    pass
                return NotificationResponse.ACK

        return NotificationResponse.NO_ACK

    def create_html_file(self):
        return f"""
        <head>
        <title>Boids</title>
        </head>
        <body>
        <canvas id="boids-canvas" width="{self._grid_size[0]}" height="{self._grid_size[1]}">
        <script>
        const wormHistory = {json.dumps(self._worm_history)};
        const boidHistory = {json.dumps(self._boid_history)};
        function drawBoid(ctx, boid) {{
            const angle = Math.atan2(boid.dy, boid.dx);
            ctx.translate(boid.x, boid.y);
            ctx.rotate(angle);
            ctx.translate(-boid.x, -boid.y);
            ctx.fillStyle = boid.full ? "gold" : "#558cf4";
            ctx.beginPath();
            ctx.moveTo(boid.x, boid.y);
            ctx.lineTo(boid.x - 15, boid.y + 5);
            ctx.lineTo(boid.x - 15, boid.y - 5);
            ctx.lineTo(boid.x, boid.y);
            ctx.fill();
            ctx.setTransform(1, 0, 0, 1, 0, 0);
        }}
        function drawWorm(ctx, x, y) {{
            ctx.beginPath();
            ctx.arc(x, y, 4, 2 * Math.PI, false);
            ctx.fillStyle = 'pink';
            ctx.fill();
        }}

        let i = 0;

        function animationLoop() {{
            // Clear the canvas and redraw all the boids in their current positions
            const ctx = document.getElementById("boids-canvas").getContext("2d");
            ctx.clearRect(0, 0, {self._grid_size[0]}, {self._grid_size[1]});
            for (let {{movement, boid_id, full}} of boidHistory[i]) {{
                drawBoid(ctx, {{
                    x: movement.position[0],
                    y: movement.position[1],
                    dx: movement.velocity[0],
                    dy: movement.velocity[1],
                    full 
                }});
            }}
            for (let [x, y] of wormHistory[i]) {{
                drawWorm(ctx, x, y)
            }}

            i += 1;
            if (i >= boidHistory.length) {{
                i = 0;
            }}
            // Schedule the next frame
            window.requestAnimationFrame(animationLoop);

        }}

        window.onload = () => {{
        // Schedule the main animation loop
        window.requestAnimationFrame(animationLoop);
        }};
        </script>
        </body>
        """


async def run_sim(use_websockets: bool = False):
    run_till = None if use_websockets else 1000
    num_boids = 10 if use_websockets else 50
    grid_size = (1000, 1000)
    if use_websockets:
        hades = HadesWS(
            random_pomegranate_seed="Reynolds", record_results=False, use_no_ack_cache=True, record_event_history=False
        )
    else:
        hades = Hades(
            random_pomegranate_seed="Reynolds", record_results=False, use_no_ack_cache=True, record_event_history=False
        )
    hades.register_process(
        process=PredefinedEventAdder(
            predefined_events=[
                BoidMoved(
                    t=0,
                    boid_id=i,
                    movement=ImmutableMovement(position=(500 - i, 500 + i), velocity=(-1 - (0.1 * i), 1 + (0.1 * i))),
                )
                for i in range(num_boids)
            ],
            name="add boids",
        )
    )
    hades.register_process(
        PredefinedEventAdder(
            predefined_events=[
                WormPopsHisHeadUp(
                    worm_id=i,
                    t=i,
                    worm_position=(
                        hades.random.randint(0, grid_size[0] - 1),
                        hades.random.randint(0, grid_size[1] - 1),
                    ),
                )
                for i in range(0, 1000, 50 if use_websockets else 5)
            ],
            name="worm spawner",
        )
    )
    hades.register_process(WormHider())
    for i in range(num_boids):
        hades.register_process(Boid(boid_identifier=i, grid_size=(1000, 1000)))

    if not use_websockets:
        movement_history = BoidMovementHistory(grid_size=(1000, 1000))
        hades.register_process(movement_history)
    await hades.run(until=run_till)

    if not use_websockets:
        with open("boids.html", "w") as f:
            f.write(movement_history.create_html_file())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run_sim(len(sys.argv) > 1 and sys.argv[1] == "websockets"))
