import numpy as np
from datetime import datetime, timedelta


class KPIUtils:
    """
    Utility functions for KPI calculations and analysis.
    """

    @staticmethod
    def calculate_weighted_score(scores, weights):
        """
        Calculate weighted score from multiple metrics.

        Args:
            scores: Dict of metric_name -> score (0-1)
            weights: Dict of metric_name -> weight

        Returns:
            float: Weighted score (0-1)
        """
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0

        weighted_sum = sum(
            scores.get(metric, 0) * weight
            for metric, weight in weights.items()
        )

        return weighted_sum / total_weight

    @staticmethod
    def normalize_score(value, min_val, max_val, higher_is_better=True):
        """
        Normalize a value to 0-1 scale.
        """
        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)

        if not higher_is_better:
            normalized = 1 - normalized

        return max(0, min(1, normalized))

    @staticmethod
    def calculate_trend(historical_values):
        """
        Calculate trend from historical values.

        Returns:
            str: 'improving', 'stable', or 'declining'
        """
        if len(historical_values) < 3:
            return 'stable'

        # Simple linear regression
        x = np.arange(len(historical_values))
        y = np.array(historical_values)

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        # Determine trend based on slope
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'

    @staticmethod
    def estimate_completion_date(current_velocity, remaining_work, sprint_duration=14):
        """
        Estimate project completion date based on velocity.
        """
        if current_velocity <= 0:
            return None

        remaining_sprints = remaining_work / current_velocity
        remaining_days = remaining_sprints * sprint_duration

        completion_date = datetime.now() + timedelta(days=remaining_days)

        return {
            'estimated_date': completion_date,
            'remaining_sprints': round(remaining_sprints, 1),
            'confidence': 'High' if remaining_sprints < 3 else 'Medium' if remaining_sprints < 6 else 'Low'
        }

    @staticmethod
    def calculate_risk_score(factors):
        """
        Calculate overall risk score from multiple risk factors.

        Args:
            factors: List of {'type': str, 'severity': str, 'probability': float}

        Returns:
            dict: Risk analysis
        """
        severity_weights = {
            'Low': 1,
            'Medium': 2,
            'High': 3,
            'Critical': 4
        }

        total_risk = 0
        high_risk_count = 0

        for factor in factors:
            severity = severity_weights.get(factor.get('severity', 'Medium'), 2)
            probability = factor.get('probability', 0.5)

            risk_value = severity * probability
            total_risk += risk_value

            if risk_value > 2:
                high_risk_count += 1

        # Normalize risk score
        max_possible_risk = len(factors) * 4  # All critical with 100% probability
        risk_percentage = (total_risk / max_possible_risk * 100) if max_possible_risk > 0 else 0

        return {
            'risk_score': round(risk_percentage, 1),
            'risk_level': 'Critical' if risk_percentage > 75 else 'High' if risk_percentage > 50 else 'Medium' if risk_percentage > 25 else 'Low',
            'high_risk_factors': high_risk_count,
            'total_factors': len(factors)
        }