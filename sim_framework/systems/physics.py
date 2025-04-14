from sim_framework.components import Position, Velocity

class PhysicsSystem:
    def __init__(self):
        self.dt = 1.0

    def process(self, world):
        for _, (pos, vel) in world.get_components(Position, Velocity):
            pos.x += vel.vx * self.dt
            pos.y += vel.vy * self.dt
            pos.z += vel.vz * self.dt
