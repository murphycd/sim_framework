from dataclasses import dataclass

@dataclass
class Velocity:
    vx: float
    vy: float
    vz: float = 0.0
