# Dynamic Dependency-Aware Temporal RCA for ROS 2

A ROS 2 diagnostic framework that discovers runtime node dependencies, correlates anomalies over time, and ranks probable root causes with supporting evidence.

## Prerequisites

- Ubuntu 24.04
- ROS 2 Jazzy
- Git, `colcon`, and `rosdep`

## Setup

### 1. Install dependencies

```bash
sudo apt update
sudo apt install -y git python3-rosdep \
  python3-colcon-common-extensions \
  python3-pytest build-essential
```

Install [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation.html) if it is not already installed.

### 2. Clone the repository

```bash
mkdir -p ~/ros2_rca_ws
cd ~/ros2_rca_ws

git clone https://github.com/iBlazeX/ros2-dynamic-temporal-rca.git .
```

### 3. Install ROS dependencies

```bash
sudo rosdep init 2>/dev/null || true
rosdep update

source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### 4. Build the workspace

```bash
colcon build --symlink-install
source install/setup.bash
```

## Run `rca_sim`

Start the simulation:

```bash
scripts/sim.sh start
```

In a second terminal, source the environment and launch the diagnostic dashboard:

```bash
cd ~/ros2_rca_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run diagnostic_tui rca_tui
```

## Inject a Test Fault

Inject a temporary LiDAR latency fault:

```bash
ros2 run rca_test_system fault_injector \
  --target lidar_node \
  --type latency \
  --param 0.4 \
  --duration 10
```

Observe the detected anomalies, runtime dependency graph, and probable root-cause diagnosis in the dashboard.

## Inspect Diagnostic Results

```bash
ros2 run diagnostic_monitor rca_cli --action graph
ros2 run diagnostic_monitor rca_cli --action latest
ros2 run diagnostic_monitor rca_cli --action summary
```

## Real Robot Integration

The monitor can be adapted to observe a real ROS 2 robot by discovering its runtime graph and monitoring its published topics. Begin with read-only monitoring before attempting controlled fault experiments.

## Project Structure

- `src/` : ROS 2 packages, simulation, monitoring, and diagnosis
- `scripts/` : Startup, benchmarking, and verification tools
- `runs/` : Experiment results and recorded evidence

## Notes

- Source the ROS environment and workspace in every new terminal.
- `rca_sim` is the simulation backend.
- Supported fault targets and types depend on the implementation.
- Root-cause results represent evidence-based rankings, not guaranteed proof of causality.
