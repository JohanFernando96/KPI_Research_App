import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import { kpiService } from "../../services/kpiService";
import { projectService } from "../../services/projectService";

const TeamAnalysisDashboard = ({ projectId, projectData, teamData }) => {
  const [analysis, setAnalysis] = useState(null);
  const [successPrediction, setSuccessPrediction] = useState(null);
  const [teamBasedKPIs, setTeamBasedKPIs] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState("overview");

  useEffect(() => {
    if (projectId && teamData?.employee_ids?.length > 0) {
      fetchTeamAnalysis();
    }
  }, [projectId, teamData]);

  const fetchTeamAnalysis = async () => {
    setIsLoading(true);
    setError("");

    try {
      // Get team-based KPIs
      const kpiResponse = await kpiService.generateTeamBasedKPIs(projectId);
      if (kpiResponse.success) {
        setTeamBasedKPIs(kpiResponse.data);
        setAnalysis(kpiResponse.data.team_analysis);
      }

      // Get success prediction
      const predictionResponse = await kpiService.predictProjectSuccess(projectId);
      if (predictionResponse.success) {
        setSuccessPrediction(predictionResponse.prediction);
      }
    } catch (error) {
      console.error("Error fetching team analysis:", error);
      setError("Failed to analyze team composition");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptimizeTeam = async () => {
    setIsLoading(true);
    try {
      const response = await projectService.optimizeTeam(projectId);
      if (response.success) {
        // Handle optimization suggestions
        console.log("Optimization suggestions:", response.suggestions);
      }
    } catch (error) {
      console.error("Error optimizing team:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderSkillCoverage = () => {
    if (!analysis?.skill_coverage) return null;

    const coverage = analysis.skill_coverage.percentage || 0;
    const getColor = (percentage) => {
      if (percentage >= 80) return "bg-green-500";
      if (percentage >= 60) return "bg-yellow-500";
      return "bg-red-500";
    };

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Skill Coverage</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Overall Coverage</span>
              <span className="text-sm font-medium">{Math.round(coverage)}%</span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full">
              <div
                className={`h-3 rounded-full ${getColor(coverage)}`}
                style={{ width: `${coverage}%` }}
              ></div>
            </div>
          </div>

          {analysis.skill_coverage.missing_skills?.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Missing Skills</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.skill_coverage.missing_skills.map((skill, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderExperienceDistribution = () => {
    if (!analysis?.experience_distribution) return null;

    const distribution = analysis.experience_distribution;
    const levels = ['Junior', 'Mid-level', 'Senior', 'Lead'];

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Experience Distribution</h3>
        <div className="space-y-2">
          {levels.map(level => {
            const count = distribution[level] || 0;
            const percentage = (count / (teamData?.employee_ids?.length || 1)) * 100;
            
            return (
              <div key={level} className="flex items-center">
                <span className="w-20 text-sm text-gray-600">{level}</span>
                <div className="flex-1 mx-2">
                  <div className="w-full h-6 bg-gray-200 rounded">
                    <div
                      className="h-6 bg-blue-500 rounded"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
                <span className="text-sm text-gray-600">{count}</span>
              </div>
            );
          })}
        </div>
        
        {distribution.balance_score && (
          <div className="mt-4 p-3 bg-blue-50 rounded">
            <p className="text-sm text-blue-800">
              Balance Score: <strong>{Math.round(distribution.balance_score * 100)}%</strong>
              {distribution.balance_score < 0.6 && (
                <span className="ml-2 text-yellow-600">⚠️ Team experience is imbalanced</span>
              )}
            </p>
          </div>
        )}
      </div>
    );
  };

  const renderSuccessPrediction = () => {
    if (!successPrediction) return null;

    const probability = successPrediction.success_probability || 0;
    const getColor = (prob) => {
      if (prob >= 0.8) return "text-green-600";
      if (prob >= 0.6) return "text-yellow-600";
      return "text-red-600";
    };

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Success Prediction</h3>
        <div className="text-center p-6 bg-gray-50 rounded-lg">
          <div className={`text-4xl font-bold ${getColor(probability)}`}>
            {Math.round(probability * 100)}%
          </div>
          <p className="text-sm text-gray-600 mt-2">Predicted Success Probability</p>
        </div>

        {successPrediction.risk_factors?.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Risk Factors</h4>
            <ul className="space-y-1">
              {successPrediction.risk_factors.map((risk, index) => (
                <li key={index} className="text-sm text-red-600">
                  • {risk}
                </li>
              ))}
            </ul>
          </div>
        )}

        {successPrediction.recommendations?.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {successPrediction.recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-green-600">
                  • {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderTeamVelocity = () => {
    if (!analysis?.velocity_estimation) return null;

    const velocity = analysis.velocity_estimation;

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Velocity Estimation</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded">
            <p className="text-sm text-gray-600">Estimated Velocity</p>
            <p className="text-2xl font-bold text-blue-800">
              {velocity.estimated_velocity} pts/sprint
            </p>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <p className="text-sm text-gray-600">Efficiency Factor</p>
            <p className="text-2xl font-bold text-green-800">
              {Math.round(velocity.efficiency_factor * 100)}%
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded">
            <p className="text-sm text-gray-600">Confidence Level</p>
            <p className="text-2xl font-bold text-purple-800">
              {velocity.confidence_level || "Medium"}
            </p>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return <Loading text="Analyzing team composition..." />;
  }

  return (
    <Card title="Team Analysis & Optimization">
      <div className="space-y-6">
        {error && (
          <div className="p-4 bg-red-50 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="flex space-x-2 border-b">
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeView === "overview"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveView("overview")}
          >
            Overview
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeView === "kpis"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveView("kpis")}
          >
            Team-Based KPIs
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeView === "optimization"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveView("optimization")}
          >
            Optimization
          </button>
        </div>

        {activeView === "overview" && analysis && (
          <div>
            {renderSkillCoverage()}
            {renderExperienceDistribution()}
            {renderTeamVelocity()}
            {renderSuccessPrediction()}
          </div>
        )}

        {activeView === "kpis" && teamBasedKPIs && (
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Team-Adjusted KPIs
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              These KPIs have been adjusted based on your team's actual composition,
              skills, and experience levels.
            </p>
            {/* Display team-based KPIs here */}
          </div>
        )}

        {activeView === "optimization" && (
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Team Optimization
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Get AI-powered suggestions to optimize your team composition.
            </p>
            <Button
              onClick={handleOptimizeTeam}
              disabled={isLoading}
              icon={
                <svg
                  className="w-4 h-4 mr-1"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              }
            >
              Optimize Team
            </Button>
          </div>
        )}

        {!teamData?.employee_ids?.length && (
          <div className="text-center py-8">
            <p className="text-gray-500">
              No team members assigned yet. Add team members to see analysis.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default TeamAnalysisDashboard;