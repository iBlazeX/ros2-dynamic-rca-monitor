import pytest

from diagnostic_monitor.missing_publisher_tracker import (
    MissingPublisherTracker,
)


def test_required_topic_escalates_only_after_grace_period():
    tracker = MissingPublisherTracker(
        required_topics={"/scan"},
        grace_period_sec=2.0,
    )

    events = tracker.update({"/scan": ["perception"]}, now=10.0)
    assert [e["event"] for e in events] == [
        "missing_publisher_observed"
    ]

    assert tracker.update(
        {"/scan": ["perception"]}, now=11.0
    ) == []

    status = tracker.current_status(now=11.0)
    assert status[0]["escalated"] is False
    assert status[0]["duration_sec"] == 1.0

    events = tracker.update({"/scan": ["perception"]}, now=12.0)
    assert [e["event"] for e in events] == [
        "required_dependency_unavailable"
    ]
    assert events[0]["duration_sec"] == 2.0

    # Escalation must happen only once per active condition.
    assert tracker.update(
        {"/scan": ["perception"]}, now=13.0
    ) == []


def test_optional_topic_never_escalates():
    tracker = MissingPublisherTracker(grace_period_sec=1.0)

    events = tracker.update({"/camera": ["viewer"]}, now=0.0)
    assert events[0]["required"] is False

    assert tracker.update({"/camera": ["viewer"]}, now=100.0) == []

    status = tracker.current_status(now=100.0)
    assert status[0]["status"] == "observed_missing_publisher"
    assert status[0]["escalated"] is False
    assert status[0]["duration_sec"] == 100.0


def test_publisher_returns_before_grace_period():
    tracker = MissingPublisherTracker(
        required_topics={"/scan"},
        grace_period_sec=2.0,
    )

    tracker.update({"/scan": ["perception"]}, now=10.0)

    events = tracker.update({}, now=11.0)
    assert [e["event"] for e in events] == [
        "missing_publisher_cleared"
    ]
    assert events[0]["duration_sec"] == 1.0
    assert events[0]["escalated"] is False
    assert tracker.current_status(now=11.0) == []


def test_recovery_after_escalation_records_duration():
    tracker = MissingPublisherTracker(
        required_topics={"/scan"},
        grace_period_sec=2.0,
    )

    tracker.update({"/scan": ["perception"]}, now=10.0)
    tracker.update({"/scan": ["perception"]}, now=12.0)

    events = tracker.update({}, now=15.0)

    assert [e["event"] for e in events] == [
        "missing_publisher_cleared"
    ]
    assert events[0]["duration_sec"] == 5.0
    assert events[0]["escalated"] is True
    assert tracker.current_status(now=15.0) == []


def test_multiple_subscribers_are_sorted_and_deduplicated():
    tracker = MissingPublisherTracker()

    events = tracker.update(
        {"/scan": ["z_node", "a_node", "a_node"]},
        now=5.0,
    )

    assert events[0]["subscribers"] == ["a_node", "z_node"]

    # Subscriber changes update the active condition.
    tracker.update({"/scan": ["b_node"]}, now=6.0)

    status = tracker.current_status(now=6.0)
    assert status[0]["subscribers"] == ["b_node"]
    assert status[0]["first_seen"] == 5.0


def test_reappearing_condition_starts_a_new_grace_period():
    tracker = MissingPublisherTracker(
        required_topics={"/scan"},
        grace_period_sec=2.0,
    )

    tracker.update({"/scan": ["perception"]}, now=0.0)
    tracker.update({}, now=1.0)

    events = tracker.update({"/scan": ["perception"]}, now=10.0)
    assert [e["event"] for e in events] == [
        "missing_publisher_observed"
    ]

    status = tracker.current_status(now=11.0)
    assert status[0]["first_seen"] == 10.0
    assert status[0]["escalated"] is False


def test_negative_grace_period_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        MissingPublisherTracker(grace_period_sec=-1.0)
