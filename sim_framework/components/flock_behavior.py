from dataclasses import dataclass

@dataclass
class FlockBehavior:
    maxSpeed: float
    neighborRadius: float
    separationWeight: float
    alignmentWeight: float
    cohesionWeight: float
