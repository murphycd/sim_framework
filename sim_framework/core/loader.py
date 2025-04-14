import yaml
from sim_framework.components import Position, Velocity, FlockBehavior

COMPONENT_CLASSES = {
    "Position": Position,
    "Velocity": Velocity,
    "FlockBehavior": FlockBehavior
}

def load_entities(world, config_path="config/entities.yaml"):
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    archetypes = data.get("archetypes", {})
    entities = data.get("entities", [])

    for ent in entities:
        eid = world.create_entity()
        archetype_name = ent.get("type")
        base = archetypes.get(archetype_name, {}).get("components", {})
        overrides = ent.get("components", {})

        components = {**base, **overrides}
        for cname, fields in components.items():
            comp_cls = COMPONENT_CLASSES.get(cname)
            if comp_cls:
                world.add_component(eid, comp_cls(**fields))
            else:
                print(f"[WARN] Unknown component: {cname}")
