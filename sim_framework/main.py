import argparse
from sim_framework.core.system_loader import load_systems
from sim_framework.core.loader import load_entities
from sim_framework.ecs.world import SimWorld

def create_world(mode="local") -> SimWorld:
    print(f"[INIT] Creating ECS world for mode: {mode}")
    return SimWorld()

def loop(world):
    tick = 0
    while True:
        print(f"[TICK {tick}]")
        world.process()
        if any(m["type"] == "ExitRequested" for m in world.messages.messages):
            print("[EXIT] ExitRequested received")
            break
        world.messages.clear()
        tick += 1

def run_local():
    world = create_world(mode="local")
    load_entities(world)
    load_systems(world)
    loop(world)

def run_server():
    pass

def run_client():
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true", help="Run as dedicated server")
    parser.add_argument("--client", action="store_true", help="Run as standalone client")
    parser.add_argument("--local", action="store_true", help="Run client and server in one process")
    args = parser.parse_args()

    if args.server:
        run_server()
    elif args.client:
        run_client()
    else:
        run_local()

if __name__ == "__main__":
    main()
