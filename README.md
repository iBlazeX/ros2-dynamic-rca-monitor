# ROS 2 Dynamic Temporal RCA

A ROS 2 diagnostic monitoring framework for tracking system health, detecting runtime dependency failures, and investigating potential root causes through dynamic graph analysis and temporal event correlation.

## Overview

ROS 2 systems are composed of interconnected nodes and topics whose runtime relationships can change as components start, stop, or fail. Diagnosing a failure requires more than identifying an unhealthy node: it also requires understanding how the system's dependencies changed over time.

**ROS 2 Dynamic Temporal RCA** aims to make these relationships observable by combining runtime graph discovery, diagnostic monitoring, and a timeline of system events.

The project explores how changes in the ROS 2 communication graph can help explain failures and identify potentially affected components.

## Key Features

- **Dynamic graph discovery:** Observe runtime relationships between ROS 2 nodes and topics.
- **Missing-publisher detection:** Detect required topics that have subscribers but no discovered publisher.
- **Explicit missing-input graph overlays:** Show unavailable topics linked to their real subscribers without inventing live publisher nodes.
- **Temporal RCA for dependency gaps:** Consider a missing publisher as an upstream candidate when it precedes and reaches observed downstream anomalies.
- **Configurable grace period:** Allow a configurable interval before reporting a missing publisher.
- **Dependency availability tracking:** Track when required topic dependencies become unavailable and recover.
- **Temporal event logging:** Record events such as missing-publisher observations, dependency unavailability, and recovery.
- **ROS 2 diagnostics integration:** Monitor system health and expose diagnostic information.
- **Graceful handling of incomplete discovery:** Avoid treating incomplete graph-discovery results as confirmed failures.

## Architecture

The framework is organized around a few core components:

| Component | Responsibility |
|---|---|
| `RosGraphDiscoverer` | Discovers the runtime ROS 2 communication graph and missing-publisher conditions. |
| `MissingPublisherTracker` | Tracks missing-publisher states and their duration. |
| `MonitorNode` | Coordinates monitoring, graph updates, and event generation. |
| Timeline events | Record dependency failures and recovery for temporal analysis. |

The overall workflow is:

1. Discover the current ROS 2 graph.
2. Compare discovered publishers and subscribers against configured requirements.
3. Track missing publishers across successive discovery cycles.
4. Report dependency failures after the configured grace period.
5. Record recovery when the missing publisher reappears.
6. Use graph changes and event timing to support root-cause investigation.

## Example: Missing Publisher Detection

Suppose a subscriber depends on `/scan`, but no publisher for that topic is available.

When `/scan` is configured as a required topic, the monitor can track the missing publisher and report the dependency as unavailable after the grace period.

When a publisher becomes visible again, the monitor records a recovery event.

Relevant timeline events include:

- `missing_publisher_observed`
- `required_dependency_unavailable`
- `missing_publisher_cleared`

This helps distinguish a temporary discovery gap from a sustained dependency failure.

## Configuration

The monitor supports the following parameters for required-topic monitoring:

| Parameter | Purpose |
|---|---|
| `required_topics` | List of topics that are expected to have publishers. |
| `missing_publisher_grace_sec` | Grace period before a missing publisher is reported as unavailable. |

Example ROS 2 parameter overrides:

```bash
-p "required_topics:=['/scan']" \
-p missing_publisher_grace_sec:=2.0
```

Use these overrides with the appropriate launch or node command for your workspace.

## Requirements

- ROS 2
- Python 3
- `colcon`
- `pytest`
- A ROS 2 workspace configured for the target distribution

Exact package dependencies may vary with the ROS 2 distribution and workspace configuration.

## Build

```bash
cd ~/ros2_rca_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select diagnostic_monitor diagnostic_tui --symlink-install
source install/setup.bash
```

## Run

Launch the diagnostic monitor, declaring `/scan` as a required topic with a two-second grace period:

```bash
ros2 launch diagnostic_monitor monitor.launch.py \
  db_path:=/tmp/diagnostic_monitor.db \
  simulator:=real_robot \
  "required_topics:=['/scan']" \
  missing_publisher_grace_sec:=2.0
```

In a separate terminal, launch the live TUI:

```bash
ros2 run diagnostic_tui rca_tui
```

The graph panel distinguishes live ROS node/edge counts from virtual missing-input overlays. A virtual source such as `/scan [missing publisher]` represents an unavailable topic dependency, not a claim that a LiDAR node is running.

## Test

```bash
cd ~/ros2_rca_ws
colcon test --packages-select diagnostic_monitor diagnostic_tui --event-handlers console_direct+
colcon test-result --verbose
```

## Research Direction

The project's central research direction is **dynamic graph analysis with temporal root-cause analysis for ROS 2 systems**.

Potential research questions include:

- How can runtime graph changes help distinguish primary failures from downstream symptoms?
- How can temporal relationships between diagnostic events improve root-cause localization?
- How should incomplete graph discovery be handled to reduce false failure reports?
- How can dependency recovery events help reconstruct the progression of a failure?

These questions provide a foundation for evaluating the framework using controlled fault-injection experiments and representative ROS 2 workloads.

## Project Status

The framework includes dynamic graph monitoring, required-topic missing-publisher tracking, timeline event generation, and automated tests.

Temporal root-cause localization beyond event tracking should be treated as ongoing research until implemented and evaluated.

## Contributing

Contributions, bug reports, and suggestions are welcome. When proposing changes, include the relevant test cases and steps to reproduce the behavior.
