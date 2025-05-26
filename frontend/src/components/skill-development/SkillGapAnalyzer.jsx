// frontend/src/components/skill-development/SkillGapAnalyzer.jsx
import React, { useState, useEffect, useCallback, useMemo } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import { recommendationService } from "../../services/recommendationService";

const SkillGapAnalyzer = ({ employeeId, employeeData, onAnalysisComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analysisType, setAnalysisType] = useState("career");
  // Cache analysis results to prevent reloading
  const [analysisCache, setAnalysisCache] = useState({});

  const handleAnalyzeSkillGap = useCallback(async (type = analysisType) => {
    // Check cache first
    if (analysisCache[type]) {
      setAnalysis(analysisCache[type]);
      if (onAnalysisComplete) {
        onAnalysisComplete(analysisCache[type]);
      }
      return;
    }

    if (!employeeId) return;

    setIsLoading(true);
    setError("");

    try {
      const currentRole = employeeData?.Experience?.[0]?.Role || "";
      
      const requestData = {
        current_role: currentRole
      };
      
      // For role analysis, ensure we have a default role if none provided
      if (type === "role") {
        requestData.role_name = currentRole || "Software Engineer";
      }

      const response = await recommendationService.analyzeSkillGap(
        employeeId,
        type,
        requestData
      );

      if (response.success) {
        // Cache the result
        setAnalysisCache(prev => ({
          ...prev,
          [type]: response.analysis
        }));
        setAnalysis(response.analysis);
        if (onAnalysisComplete) {
          onAnalysisComplete(response.analysis);
        }
      } else {
        setError(response.message || "Failed to analyze skill gap");
      }
    } catch (error) {
      console.error("Error analyzing skill gap:", error);
      setError("An error occurred while analyzing skill gap");
    } finally {
      setIsLoading(false);
    }
  }, [employeeId, employeeData, analysisType, analysisCache, onAnalysisComplete]);

  useEffect(() => {
    if (employeeId && !analysisCache[analysisType]) {
      handleAnalyzeSkillGap(analysisType);
    } else if (analysisCache[analysisType]) {
      setAnalysis(analysisCache[analysisType]);
    }
  }, [employeeId, analysisType]);

  const renderCareerAnalysis = () => {
    if (!analysis) return null;

    const { current_role, next_role, readiness, skill_gaps } = analysis;
    const readinessPercentage = Math.round((readiness || 0) * 100);

    // Handle both old and new API response formats
    const nextRoleTitle = analysis.next_role_details?.role_title || next_role;
    const skillGapsData = analysis.next_role_details?.skill_gaps || skill_gaps || {};

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 mb-6 md:grid-cols-3">
          <div className="p-4 bg-white rounded-md shadow">
            <h3 className="mb-1 text-sm font-medium text-gray-700">
              Current Role
            </h3>
            <p className="text-lg font-semibold text-gray-900">
              {current_role || "Unknown"}
            </p>
          </div>

          <div className="p-4 bg-white rounded-md shadow">
            <h3 className="mb-1 text-sm font-medium text-gray-700">
              Next Role
            </h3>
            <p className="text-lg font-semibold text-gray-900">
              {nextRoleTitle || "Highest Level"}
            </p>
          </div>

          <div className="p-4 bg-white rounded-md shadow">
            <h3 className="mb-1 text-sm font-medium text-gray-700">
              Readiness
            </h3>
            <div className="flex items-center">
              <div className="flex-grow h-2 mr-2 bg-gray-200 rounded-full">
                <div
                  className={`h-full rounded-full ${
                    readinessPercentage >= 70
                      ? "bg-green-500"
                      : readinessPercentage >= 40
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${readinessPercentage}%` }}
                ></div>
              </div>
              <span className="text-lg font-semibold text-gray-900">
                {readinessPercentage}%
              </span>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-md shadow">
          <h3 className="mb-3 font-medium text-gray-800">
            Skill Gaps for Next Role
          </h3>

          {skillGapsData && (
            <div className="space-y-4">
              {skillGapsData.technical && skillGapsData.technical.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">
                    Technical Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {skillGapsData.technical.map((skill, index) => {
                      const skillName = typeof skill === 'string' ? skill : skill.name || skill;
                      return (
                        <span
                          key={index}
                          className="bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded"
                        >
                          {skillName}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {skillGapsData.soft && skillGapsData.soft.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">
                    Soft Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {skillGapsData.soft.map((skill, index) => {
                      const skillName = typeof skill === 'string' ? skill : skill.name || skill;
                      return (
                        <span
                          key={index}
                          className="bg-purple-100 text-purple-800 text-xs px-2.5 py-1 rounded"
                        >
                          {skillName}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {skillGapsData.domain && skillGapsData.domain.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">
                    Domain Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {skillGapsData.domain.map((skill, index) => {
                      const skillName = typeof skill === 'string' ? skill : skill.name || skill;
                      return (
                        <span
                          key={index}
                          className="bg-green-100 text-green-800 text-xs px-2.5 py-1 rounded"
                        >
                          {skillName}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {(!skillGapsData ||
            (!skillGapsData.technical?.length && 
             !skillGapsData.soft?.length && 
             !skillGapsData.domain?.length)) && (
            <p className="text-gray-500">
              No skill gaps identified for the next role.
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderRoleAnalysis = () => {
    if (!analysis || !analysis.role) return null;

    const {
      role,
      technical = {},
      soft = {},
      overall_coverage = 0,
      is_qualified = false,
    } = analysis;

    const technicalData = {
      coverage: technical?.total_coverage || technical?.coverage || 0,
      gaps: technical?.gaps || [],
      matches: technical?.matches || [],
    };

    const softData = {
      coverage: soft?.total_coverage || soft?.coverage || 0,
      gaps: soft?.gaps || [],
      matches: soft?.matches || [],
    };

    const coveragePercentage = Math.round(overall_coverage * 100);

    return (
      <div className="space-y-4">
        <div className="p-4 bg-white rounded-md shadow">
          <h3 className="mb-2 font-medium text-gray-800">
            Role Analysis: {role}
          </h3>

          <div className="mb-4">
            <h4 className="mb-1 text-sm font-medium text-gray-700">
              Overall Coverage
            </h4>
            <div className="flex items-center">
              <div className="flex-grow h-2 mr-2 bg-gray-200 rounded-full">
                <div
                  className={`h-full rounded-full ${
                    coveragePercentage >= 70
                      ? "bg-green-500"
                      : coveragePercentage >= 40
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${coveragePercentage}%` }}
                ></div>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {coveragePercentage}%
              </span>
            </div>
          </div>

          <div className="flex items-center mb-4">
            <span className="mr-2 text-sm text-gray-700">
              Qualification Status:
            </span>
            <span
              className={`text-xs px-2.5 py-0.5 rounded ${
                is_qualified
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {is_qualified ? "Qualified" : "Not Qualified"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="p-4 bg-white rounded-md shadow">
            <h3 className="mb-3 font-medium text-gray-800">Technical Skills</h3>

            <div className="mb-2">
              <div className="flex justify-between mb-1 text-xs text-gray-500">
                <span>Coverage</span>
                <span>{Math.round(technicalData.coverage * 100)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${technicalData.coverage * 100}%` }}
                ></div>
              </div>
            </div>

            {technicalData.gaps.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-700">
                  Missing Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {technicalData.gaps.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-red-100 text-red-800 text-xs px-2.5 py-1 rounded"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {technicalData.matches.length > 0 && (
              <div className="mt-3">
                <h4 className="mb-2 text-sm font-medium text-gray-700">
                  Matching Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {technicalData.matches.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-green-100 text-green-800 text-xs px-2.5 py-1 rounded"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-white rounded-md shadow">
            <h3 className="mb-3 font-medium text-gray-800">Soft Skills</h3>

            <div className="mb-2">
              <div className="flex justify-between mb-1 text-xs text-gray-500">
                <span>Coverage</span>
                <span>{Math.round(softData.coverage * 100)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full">
                <div
                  className="h-full bg-purple-500 rounded-full"
                  style={{ width: `${softData.coverage * 100}%` }}
                ></div>
              </div>
            </div>

            {softData.gaps.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-700">
                  Missing Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {softData.gaps.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-red-100 text-red-800 text-xs px-2.5 py-1 rounded"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {softData.matches.length > 0 && (
              <div className="mt-3">
                <h4 className="mb-2 text-sm font-medium text-gray-700">
                  Matching Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {softData.matches.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-green-100 text-green-800 text-xs px-2.5 py-1 rounded"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card
      title="Skill Gap Analysis"
      subtitle="Analyze skill gaps against roles or career progression paths"
    >
      <div className="space-y-6">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={analysisType === "career" ? "primary" : "outline"}
            size="sm"
            onClick={() => setAnalysisType("career")}
          >
            Career Progression
          </Button>
          <Button
            variant={analysisType === "role" ? "primary" : "outline"}
            size="sm"
            onClick={() => setAnalysisType("role")}
          >
            Role Requirements
          </Button>
        </div>

        {isLoading ? (
          <div className="py-8">
            <Loading text="Analyzing skill gaps..." />
          </div>
        ) : error ? (
          <div className="p-4 text-red-700 rounded-md bg-red-50">
            <p>{error}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => handleAnalyzeSkillGap(analysisType)}
            >
              Retry
            </Button>
          </div>
        ) : (
          <div>
            {analysisType === "career" ? renderCareerAnalysis() : renderRoleAnalysis()}
          </div>
        )}
      </div>
    </Card>
  );
};

export default SkillGapAnalyzer;