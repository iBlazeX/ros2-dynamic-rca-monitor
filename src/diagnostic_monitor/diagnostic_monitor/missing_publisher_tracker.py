"""Track missing-publisher observations and required-topic escalation."""

from time import monotonic
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


class MissingPublisherTracker:
    """Track dependency gaps without treating them as confirmed root causes."""

    def __init__(
        self,
        required_topics: Iterable[str] = (),
        grace_period_sec: float = 2.0,
    ):
        grace_period_sec = float(grace_period_sec)
        if grace_period_sec < 0:
            raise ValueError("grace_period_sec must be non-negative")

        self.required_topics = frozenset(
            topic for topic in (required_topics or ()) if topic
        )
        self.grace_period_sec = grace_period_sec
        self._active: Dict[str, Dict[str, Any]] = {}

    def update(
        self,
        observations: Mapping[str, Sequence[str]],
        now: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Update observations and return dependency-state transition events.

        `now` is an injectable monotonic timestamp for deterministic tests.
        An observation disappears when the discovery method no longer reports
        that topic as missing a publisher.
        """
        timestamp = monotonic() if now is None else float(now)

        current = {}
        for topic, subscribers in observations.items():
            if not topic:
                continue
            names = sorted({name for name in subscribers if name})
            if names:
                current[topic] = names

        events = []

        # A previously missing-publisher condition is no longer observed.
        for topic in sorted(set(self._active) - set(current)):
            state = self._active.pop(topic)
            events.append({
                'event': 'missing_publisher_cleared',
                'topic': topic,
                'subscribers': state['subscribers'],
                'required': state['required'],
                'escalated': state['escalated'],
                'first_seen': state['first_seen'],
                'duration_sec': max(0.0, timestamp - state['first_seen']),
            })

        for topic, subscribers in sorted(current.items()):
            state = self._active.get(topic)

            if state is None:
                state = {
                    'first_seen': timestamp,
                    'subscribers': subscribers,
                    'required': topic in self.required_topics,
                    'escalated': False,
                }
                self._active[topic] = state

                events.append({
                    'event': 'missing_publisher_observed',
                    'topic': topic,
                    'subscribers': subscribers,
                    'required': state['required'],
                    'duration_sec': 0.0,
                })
            else:
                state['subscribers'] = subscribers

            duration = max(0.0, timestamp - state['first_seen'])

            if (
                state['required']
                and not state['escalated']
                and duration >= self.grace_period_sec
            ):
                state['escalated'] = True
                events.append({
                    'event': 'required_dependency_unavailable',
                    'topic': topic,
                    'subscribers': subscribers,
                    'required': True,
                    'duration_sec': duration,
                })

        return events

    def current_status(
        self, now: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Return a snapshot of active missing-publisher conditions."""
        timestamp = monotonic() if now is None else float(now)

        statuses = []
        for topic, state in sorted(self._active.items()):
            statuses.append({
                'topic': topic,
                'subscribers': list(state['subscribers']),
                'required': state['required'],
                'first_seen': state['first_seen'],
                'duration_sec': max(
                    0.0, timestamp - state['first_seen']
                ),
                'escalated': state['escalated'],
                'status': (
                    'required_dependency_unavailable'
                    if state['escalated']
                    else 'observed_missing_publisher'
                ),
            })

        return statuses
