from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class MissingThresholdConsensusError(ValueError):
    """Raised when machinery discrepancy thresholds have not been approved."""


@dataclass(frozen=True)
class VariableThreshold:
    variable_name: str
    min_value: float | None = None
    max_value: float | None = None
    max_delta_per_hour: float | None = None
    severity: str = "medium"

    def validate(self) -> None:
        if self.min_value is None and self.max_value is None and self.max_delta_per_hour is None:
            raise MissingThresholdConsensusError(
                f"Threshold for {self.variable_name!r} has no approved bounds."
            )


@dataclass(frozen=True)
class Discrepancy:
    variable_name: str
    observed_value: float
    reason: str
    severity: str


def require_thresholds(
    thresholds: Mapping[str, VariableThreshold] | None,
    required_variables: set[str],
) -> Mapping[str, VariableThreshold]:
    if not thresholds:
        raise MissingThresholdConsensusError(
            "Approved machinery thresholds are required before discrepancy validation."
        )

    missing = sorted(required_variables.difference(thresholds))
    if missing:
        raise MissingThresholdConsensusError(
            "Missing approved thresholds for variables: " + ", ".join(missing)
        )

    for threshold in thresholds.values():
        threshold.validate()

    return thresholds


def validate_observation_discrepancies(
    observation: Mapping[str, float | int | None],
    thresholds: Mapping[str, VariableThreshold] | None,
) -> list[Discrepancy]:
    present_variables = {key for key, value in observation.items() if value is not None}
    approved_thresholds = require_thresholds(thresholds, present_variables)
    findings: list[Discrepancy] = []

    for variable_name in sorted(present_variables):
        value = float(observation[variable_name])
        threshold = approved_thresholds[variable_name]

        if threshold.min_value is not None and value < threshold.min_value:
            findings.append(
                Discrepancy(
                    variable_name=variable_name,
                    observed_value=value,
                    reason=f"below minimum {threshold.min_value}",
                    severity=threshold.severity,
                )
            )

        if threshold.max_value is not None and value > threshold.max_value:
            findings.append(
                Discrepancy(
                    variable_name=variable_name,
                    observed_value=value,
                    reason=f"above maximum {threshold.max_value}",
                    severity=threshold.severity,
                )
            )

    return findings


def validate_observation_transition_discrepancies(
    previous_observation: Mapping[str, float | int | None],
    current_observation: Mapping[str, float | int | None],
    elapsed_hours: float,
    thresholds: Mapping[str, VariableThreshold] | None,
) -> list[Discrepancy]:
    if elapsed_hours <= 0:
        raise ValueError("elapsed_hours must be greater than zero.")

    comparable_variables = {
        key
        for key, value in current_observation.items()
        if value is not None and previous_observation.get(key) is not None
    }
    approved_thresholds = require_thresholds(thresholds, comparable_variables)
    findings: list[Discrepancy] = []

    for variable_name in sorted(comparable_variables):
        threshold = approved_thresholds[variable_name]
        if threshold.max_delta_per_hour is None:
            continue

        previous_value = float(previous_observation[variable_name])
        current_value = float(current_observation[variable_name])
        delta_per_hour = abs(current_value - previous_value) / elapsed_hours

        if delta_per_hour > threshold.max_delta_per_hour:
            findings.append(
                Discrepancy(
                    variable_name=variable_name,
                    observed_value=current_value,
                    reason=f"delta per hour {delta_per_hour:.4f} exceeds {threshold.max_delta_per_hour}",
                    severity=threshold.severity,
                )
            )

    return findings
