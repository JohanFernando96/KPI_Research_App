import React from "react";

const TeamHealthIndicator = ({ analysis, prediction }) => {
  if (!analysis || !prediction) return null;

  const getHealthColor = (score) => {
    if (score >= 0.8) return "bg-green-500";
    if (score >= 0.6) return "bg-yellow-500";
    return "bg-red-500";
  };

  const overallHealth = (
    (analysis.skill_coverage.percentage / 100) * 0.4 +
    (analysis.experience_distribution.balance_score || 0.5) * 0.3 +
    (prediction.success_probability || 0.5) * 0.3
  );

  return (
    <div className="flex items-center space-x-2">
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${getHealthColor(overallHealth)}`}></div>
        {overallHealth < 0.6 && (
          <div className="absolute inset-0 w-3 h-3 rounded-full animate-ping opacity-75 bg-red-500"></div>
        )}
      </div>
      <span className="text-sm text-gray-600">
        Team Health: {Math.round(overallHealth * 100)}%
      </span>
    </div>
  );
};

export default TeamHealthIndicator;