import React, { useState, useEffect, useCallback } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import { recommendationService } from "../../services/recommendationService";

const RecommendationList = ({ employeeId, employeeData, analysis, onRecommendationsLoaded }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [recommendations, setRecommendations] = useState(null);
  const [recommendationType, setRecommendationType] = useState("career");
  const [recommendationCache, setRecommendationCache] = useState({});

  const handleGetRecommendations = useCallback(async (type = recommendationType) => {
    // Check cache first
    if (recommendationCache[type]) {
      setRecommendations(recommendationCache[type]);
      if (onRecommendationsLoaded) {
        onRecommendationsLoaded(recommendationCache[type]);
      }
      return;
    }

    if (!employeeId) return;

    setIsLoading(true);
    setError("");

    try {
      const currentRole = employeeData?.Experience?.[0]?.Role || "";
      let requestData = {
        current_role: currentRole,
      };

      // IMPORTANT: Use the analysis data to ensure consistency
      if (analysis) {
        // Pass the next role from analysis to ensure consistency
        if (analysis.next_role_details?.role_title) {
          requestData.target_role = analysis.next_role_details.role_title;
        } else if (analysis.next_role) {
          requestData.target_role = analysis.next_role;
        }

        // Pass skill gaps from analysis
        if (analysis.next_role_details?.skill_gaps) {
          const gaps = analysis.next_role_details.skill_gaps;
          const allGaps = [
            ...(gaps.technical || []),
            ...(gaps.soft || []),
            ...(gaps.domain || [])
          ];
          requestData.skill_gaps = allGaps;
        } else if (analysis.skill_gaps) {
          const allGaps = [
            ...(analysis.skill_gaps.technical || []),
            ...(analysis.skill_gaps.soft || []),
            ...(analysis.skill_gaps.domain || [])
          ];
          requestData.skill_gaps = allGaps;
        }
      }

      const response = await recommendationService.getRecommendations(
        employeeId,
        type,
        requestData
      );

      if (response.success) {
        // Ensure we use the same next role from analysis
        if (analysis && response.recommendations) {
          response.recommendations.next_role = analysis.next_role_details?.role_title || analysis.next_role;
          response.recommendations.current_role = analysis.current_role;
          response.recommendations.readiness = analysis.readiness || analysis.readiness_score || 0;
        }

        // Cache the result
        setRecommendationCache(prev => ({
          ...prev,
          [type]: response.recommendations
        }));
        setRecommendations(response.recommendations);
        if (onRecommendationsLoaded) {
          onRecommendationsLoaded(response.recommendations);
        }
      } else {
        setError(response.message || "Failed to get recommendations");
      }
    } catch (error) {
      console.error("Error getting recommendations:", error);
      setError("An error occurred while getting recommendations");
    } finally {
      setIsLoading(false);
    }
  }, [employeeId, employeeData, analysis, recommendationType, recommendationCache, onRecommendationsLoaded]);

  useEffect(() => {
    if (employeeId && !recommendationCache[recommendationType]) {
      handleGetRecommendations(recommendationType);
    } else if (recommendationCache[recommendationType]) {
      setRecommendations(recommendationCache[recommendationType]);
    }
  }, [employeeId, recommendationType, analysis]); // Added analysis as dependency

  const renderResourceItem = (resource) => {
    const resourceUrl = resource.url || resource.estimated_url || '#';
    const resourceCost = resource.cost || resource.price_range || 'Unknown';
    const resourceDuration = resource.duration || resource.estimated_time || 'Varies';
    
    return (
      <div className="p-3 bg-white border rounded-md shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex-grow">
            <h4 className="text-sm font-medium text-gray-800">
              {resource.name}
            </h4>
            <p className="mt-1 text-xs text-gray-600">{resource.provider}</p>
          </div>
          <span
            className={`text-xs px-2 py-0.5 rounded ${
              resource.type === "Course"
                ? "bg-blue-100 text-blue-800"
                : resource.type === "Book"
                ? "bg-purple-100 text-purple-800"
                : resource.type === "Tutorial"
                ? "bg-green-100 text-green-800"
                : resource.type === "Documentation"
                ? "bg-yellow-100 text-yellow-800"
                : "bg-gray-100 text-gray-800"
            }`}
          >
            {resource.type}
          </span>
        </div>

        {resource.description && (
          <p className="mt-2 text-xs text-gray-600 line-clamp-2">{resource.description}</p>
        )}

        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center space-x-3 text-xs text-gray-500">
            <span className="flex items-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {resourceDuration}
            </span>
            <span className="flex items-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {resourceCost}
            </span>
            {resource.rating && (
              <span className="flex items-center">
                <svg className="w-3 h-3 mr-1 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {resource.rating}
              </span>
            )}
          </div>
          
          {resourceUrl && resourceUrl !== '#' && (
            <a
              href={resourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              View &rarr;
            </a>
          )}
        </div>
      </div>
    );
  };

  const renderCareerRecommendations = () => {
    if (!recommendations) {
      return (
        <p className="text-gray-500">
          No recommendations available. Please complete skill gap analysis first.
        </p>
      );
    }

    // Use data from analysis to ensure consistency
    const nextRole = recommendations.next_role || analysis?.next_role_details?.role_title || analysis?.next_role;
    const currentRole = recommendations.current_role || analysis?.current_role;
    const readiness = recommendations.readiness || analysis?.readiness || 0;
    
    const courses = recommendations.courses || {};
    const technicalCourses = courses.technical || recommendations.technical || {};
    const softCourses = courses.soft || recommendations.soft || {};
    
    return (
      <div className="space-y-6">
        {nextRole && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Current Role</p>
                <p className="font-medium text-gray-800">{currentRole || 'Unknown'}</p>
              </div>
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              <div>
                <p className="text-xs text-gray-600">Next Role</p>
                <p className="font-medium text-gray-800">{nextRole}</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-600">Readiness Progress</span>
                <span className="text-xs font-medium text-gray-800">{Math.round(readiness * 100)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full">
                <div
                  className={`h-full rounded-full transition-all ${
                    readiness >= 0.7
                      ? "bg-green-500"
                      : readiness >= 0.4
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${readiness * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {Object.keys(technicalCourses).length > 0 && (
          <div>
            <h3 className="mb-3 font-medium text-gray-800 text-md flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              Technical Skills Recommendations
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {Object.entries(technicalCourses).map(
                ([skill, resources]) => (
                  <div key={skill} className="space-y-3">
                    <h4 className="text-sm font-medium text-blue-700 border-b pb-1">
                      {skill}
                    </h4>
                    {Array.isArray(resources) && resources.map((resource, idx) => (
                      <div key={idx}>{renderResourceItem(resource)}</div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {Object.keys(softCourses).length > 0 && (
          <div className="mt-6">
            <h3 className="mb-3 font-medium text-gray-800 text-md flex items-center">
              <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Soft Skills Recommendations
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {Object.entries(softCourses).map(
                ([skill, resources]) => (
                  <div key={skill} className="space-y-3">
                    <h4 className="text-sm font-medium text-purple-700 border-b pb-1">
                      {skill}
                    </h4>
                    {Array.isArray(resources) && resources.map((resource, idx) => (
                      <div key={idx}>{renderResourceItem(resource)}</div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {recommendations.learning_path && recommendations.learning_path.phases && (
          <div className="mt-6">
            <h3 className="mb-3 font-medium text-gray-800 text-md flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              Recommended Learning Path
            </h3>
            <div className="space-y-4">
              {recommendations.learning_path.phases.map((phase, idx) => (
                <div key={idx} className="relative pl-8">
                  <div className="absolute left-0 top-0 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                    {idx + 1}
                  </div>
                  {idx < recommendations.learning_path.phases.length - 1 && (
                    <div className="absolute left-3 top-6 w-0.5 h-full bg-gray-300"></div>
                  )}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-800">{phase.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">Duration: {phase.duration}</p>
                    {phase.skills && phase.skills.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-700">Focus Skills:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {phase.skills.map((skill, skillIdx) => (
                            <span
                              key={skillIdx}
                              className="px-2 py-0.5 text-xs bg-white rounded border border-gray-200"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSkillGapRecommendations = () => {
    if (!recommendations || Object.keys(recommendations).length === 0) {
      return (
        <p className="text-gray-500">
          No recommendations available for identified skill gaps.
        </p>
      );
    }

    const recommendationData = recommendations.high_priority || recommendations;

    return (
      <div className="space-y-6">
        {Object.entries(recommendationData).map(([skill, resources]) => {
          if (!Array.isArray(resources)) return null;
          
          return (
            <div key={skill} className="space-y-3">
              <h3 className="font-medium text-gray-800 text-md">{skill}</h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {resources.map((resource, idx) => (
                  <div key={idx}>{renderResourceItem(resource)}</div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!recommendations) return null;

    if (recommendationType === "career") {
      return renderCareerRecommendations();
    } else if (recommendationType === "skill_gaps") {
      return renderSkillGapRecommendations();
    }

    return null;
  };

  return (
    <Card
      title="Learning Recommendations"
      subtitle="Personalized training recommendations based on skill gaps"
    >
      <div className="space-y-6">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={recommendationType === "career" ? "primary" : "outline"}
            size="sm"
            onClick={() => setRecommendationType("career")}
          >
            Career Path
          </Button>
          <Button
            variant={
              recommendationType === "skill_gaps" ? "primary" : "outline"
            }
            size="sm"
            onClick={() => setRecommendationType("skill_gaps")}
          >
            Skill Gaps
          </Button>
        </div>

        {isLoading ? (
          <div className="py-8">
            <Loading text="Finding learning resources..." />
          </div>
        ) : error ? (
          <div className="p-4 text-red-700 rounded-md bg-red-50">
            <p>{error}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => handleGetRecommendations(recommendationType)}
            >
              Retry
            </Button>
          </div>
        ) : (
          <div className="mt-4">{renderRecommendations()}</div>
        )}
      </div>
    </Card>
  );
};

export default RecommendationList;