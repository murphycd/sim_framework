# sim_framework

**AI-driven simulation framework** designed for modular, data-driven development.  
This project is built with iterative GPT-assisted development as a core methodology.

---

## 🧠 Project Purpose

1. **AI-Native Development**  
   Optimized for AI collaboration with structured design data (`design/design.yaml`) and modular, configuration-first architecture.

2. **Generic Simulation Architecture**  
   Baseline framework for ECS-based simulations with optional physics, networking, rendering, and AI logic.

3. **Flocking Simulation**  
   Initial application: Boids-style bird flocking system modeled in 3D space with 2D output.

---

## 🚀 Getting Started

### Requirements
- Docker
- Visual Studio Code
- Dev Containers extension

### Setup
1. Clone the repo and open in VS Code.
2. Open the Command Palette → `Dev Containers: Reopen in Container`.
3. Wait for setup and install dependencies.

### Development Workflow

```bash
make run          # run the simulation
make test         # run any available tests
make lint         # run code linting (flake8)
```

Configuration lives in:
- `config/sim.yaml` — controls system loading and behavior
- `config/entities.yaml` — defines entity archetypes and instances
- `design/design.yaml` — full AI-readable project specification
