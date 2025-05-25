import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import { employeeService } from "../../services/employeeService";

const RoleAlignmentView = ({ employeeId, roleData, projectContext }) => {
  const [alignment, setAlignment] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (employeeId && roleData) {
      fetchRoleAlignment();
    }
  }, [employeeId, roleData]);

  const fetchRoleAlignment = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await employeeService.analyzeRoleAlignment(employeeId, {
        role_criteria: roleData,
        project_context: projectContext
      });

      if (response.success) {
        setAlignment(response.alignment);
      } else {
        setError(response.message || "Failed to analyze role alignment");
      }
    } catch (error) {
      console.error("Error analyzing role alignment:", error);
      setError("An error occurred while analyzing role alignment");
    } finally {
      setIsLoading(false);
    }
  };

  const renderAlignmentScore = () => {
    if (!alignment) return null;

    const score = alignment.overall_score || 0;
    const getColor = (score) => {
      if (score >= 80) return "text-green-600";
      if (score >= 60) return "text-yellow-600";
      return "text-red-600";
    };

    return (
      <div className="text-center mb-6">
        <div className={`text-5xl font-bold ${getColor(score)}`}>
          {Math.round(score)}%
        </div>
        <p className="text-gray-600 mt-2">Role Alignment Score</p>
      </div>
    );
  };

  const renderSkillAlignment = () => {
    if (!alignment?.skill_alignment) return null;

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Skill Alignment</h3>
        <div className="space-y-3">
          {alignment.skill_alignment.required_skills?.map((skill, index) => {
            const match = alignment.skill_alignment.skill_matches?.[skill];
            const hasSkill = match?.has_skill || false;
            const similarity = match?.similarity || 0;

            return (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{skill}</span>
                <div className="flex items-center">
                  {hasSkill ? (
                    <span className="text-green-600 text-sm">
                      ✓ Match ({Math.round(similarity * 100)}%)
                    </span>
                  ) : (
                    <span className="text-red-600 text-sm">✗ Missing</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderProficiencyLevel = () => {
    if (!alignment?.proficiency_level) return null;

    const level = alignment.proficiency_level;
    const getLevelColor = (level) => {
      switch (level) {
        case 'Expert': return 'bg-purple-100 text-purple-800';
        case 'Advanced': return 'bg-blue-100 text-blue-800';
        case 'Intermediate': return 'bg-green-100 text-green-800';
        case 'Beginner': return 'bg-yellow-100 text-yellow-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Proficiency Level</h3>
        <div className="flex items-center justify-between">
          <span className={`px-3 py-1 rounded text-sm font-medium ${getLevelColor(level.level)}`}>
            {level.level}
          </span>
          <span className="text-sm text-gray-600">
            {level.description}
          </span>
        </div>
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!alignment?.recommendations?.length) return null;

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Recommendations</h3>
        <ul className="space-y-2">
          {alignment.recommendations.map((rec, index) => (
            <li key={index} className="text-sm text-gray-700">
              • {rec}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  if (isLoading) {
    return <Loading text="Analyzing role alignment..." />;
  }

  return (
    <Card title="Role Alignment Analysis">
      {error ? (
        <div className="p-4 bg-red-50 text-red-700 rounded">
          {error}
        </div>
      ) : alignment ? (
        <div>
          {renderAlignmentScore()}
          {renderSkillAlignment()}
          {renderProficiencyLevel()}
          {renderRecommendations()}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-500">No alignment data available</p>
        </div>
      )}
    </Card>
  );
};

export default RoleAlignmentView;