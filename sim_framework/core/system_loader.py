import yaml
from sim_framework.systems.lifecycle import LifecycleSystem
from sim_framework.systems.flock import FlockBehaviorSystem
from sim_framework.systems.physics import PhysicsSystem
from sim_framework.systems.render import RenderSystem

SYSTEM_REGISTRY = {
    "LifecycleSystem": LifecycleSystem,
    "FlockBehaviorSystem": FlockBehaviorSystem,
    "PhysicsSystem": PhysicsSystem,
    "RenderSystem": RenderSystem,
}

def load_systems(world, config_path="config/sim.yaml"):
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    for system_def in data.get("systems", []):
        if not system_def.get("enabled", True):
            continue
        name = system_def["name"]
        config = system_def.get("config", {})
        cls = SYSTEM_REGISTRY.get(name)
        if cls:
            world.add_system(cls(**config))
        else:
            print(f"[WARN] Unknown system: {name}")
