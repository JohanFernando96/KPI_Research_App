import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SkillGapAnalyzer from "../components/skill-development/SkillGapAnalyzer";
import RecommendationList from "../components/skill-development/RecommendationList";
import TrainingResourceList from "../components/skill-development/TrainingResourceList";
import DevelopmentTracker from "../components/skill-development/DevelopmentTracker";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Loading from "../components/common/Loading";
import Modal from "../components/common/Modal";
import { employeeService } from "../services/employeeService";
import { recommendationService } from "../services/recommendationService";

const SkillDevelopmentPage = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();

  const [employee, setEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState("analysis");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [skillGapAnalysis, setSkillGapAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [developmentPlans, setDevelopmentPlans] = useState([]);
  const [activePlanId, setActivePlanId] = useState(null);
  const [showCreatePlanModal, setShowCreatePlanModal] = useState(false);
  const [selectedSkillGaps, setSelectedSkillGaps] = useState([]);
  const [selectedResources, setSelectedResources] = useState({});
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);
  const [createPlanError, setCreatePlanError] = useState("");
  
  // New states for data loading management
  const [isInitializing, setIsInitializing] = useState(false);
  const [initializationMessage, setInitializationMessage] = useState("Initializing...");
  const [dataCache, setDataCache] = useState({
    careerAnalysis: null,
    roleAnalysis: null,
    careerRecommendations: null,
    skillGapRecommendations: null,
    resourceRecommendations: null,
    lastFetched: null
  });

  // Initialize all data only when employeeId is present
  useEffect(() => {
    if (employeeId) {
      initializeAllData();
    }
  }, [employeeId]);

  // Updated extractAllSkillGaps function with better error handling
  const extractAllSkillGaps = (analysis) => {
    if (!analysis) return null;
    
    const gaps = [];
    
    // Handle new API format with next_role_details
    if (analysis.next_role_details?.skill_gaps) {
      const skillGaps = analysis.next_role_details.skill_gaps;
      const technicalGaps = (skillGaps.technical || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      const softGaps = (skillGaps.soft || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      const domainGaps = (skillGaps.domain || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      gaps.push(...technicalGaps, ...softGaps, ...domainGaps);
    } 
    // Handle old API format
    else if (analysis.skill_gaps) {
      const technicalGaps = (analysis.skill_gaps.technical || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      const softGaps = (analysis.skill_gaps.soft || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      const domainGaps = (analysis.skill_gaps.domain || []).map(g => {
        if (typeof g === 'string') return g;
        if (typeof g === 'object' && g.name) return g.name;
        return g?.toString() || '';
      });
      gaps.push(...technicalGaps, ...softGaps, ...domainGaps);
    }
    
    // Remove duplicates and filter out empty values
    const uniqueGaps = [...new Set(gaps)].filter(gap => gap && gap.trim());
    
    // If no gaps found, return null to indicate we should skip skill gap recommendations
    return uniqueGaps.length > 0 ? uniqueGaps : null;
  };

  // Updated initializeAllData function with better error handling
  const initializeAllData = async () => {
    setIsInitializing(true);
    setError("");

    try {
      // Step 1: Load employee data
      setInitializationMessage("Loading employee information...");
      const employeeResponse = await employeeService.getEmployee(employeeId);
      
      if (!employeeResponse.success) {
        throw new Error(employeeResponse.message || "Failed to load employee data");
      }
      
      setEmployee(employeeResponse.data);
      const currentRole = employeeResponse.data?.Experience?.[0]?.Role || "";

      // Step 2: Load skill gap analyses
      setInitializationMessage("Analyzing skill gaps and career progression...");
      const [careerAnalysis, roleAnalysis] = await Promise.all([
        recommendationService.analyzeSkillGap(employeeId, "career", { current_role: currentRole }),
        recommendationService.analyzeSkillGap(employeeId, "role", { 
          role_name: currentRole || "Software Engineer",
          current_role: currentRole 
        })
      ]);

      // Step 3: Load recommendations
      setInitializationMessage("Finding personalized training recommendations...");
      
      // Extract skill gaps from career analysis
      const allSkillGaps = extractAllSkillGaps(careerAnalysis.analysis);
      
      // Prepare promises for recommendations
      const recommendationPromises = [
        recommendationService.getRecommendations(employeeId, "career", { 
          current_role: currentRole,
          target_role: careerAnalysis.analysis?.next_role_details?.role_title || careerAnalysis.analysis?.next_role,
          skill_gaps: allSkillGaps || []
        })
      ];

      // Only fetch skill gap recommendations if we have actual skill gaps
      let skillRecs = { success: true, recommendations: {} };
      if (allSkillGaps && allSkillGaps.length > 0) {
        try {
          skillRecs = await recommendationService.getRecommendations(employeeId, "skill_gaps", {
            skill_gaps: allSkillGaps,
            current_role: currentRole
          });
        } catch (error) {
          console.warn("Failed to fetch skill gap recommendations:", error);
          // Continue without skill gap recommendations
        }
      }

      const [careerRecs] = await Promise.all(recommendationPromises);

      // Step 4: Load development plans
      setInitializationMessage("Loading development plans...");
      const plansResponse = await recommendationService.getEmployeeDevelopmentPlans(employeeId);

      // Update cache
      const cacheData = {
        careerAnalysis: careerAnalysis.analysis,
        roleAnalysis: roleAnalysis.analysis,
        careerRecommendations: careerRecs.recommendations,
        skillGapRecommendations: skillRecs.recommendations,
        resourceRecommendations: {
          ...careerRecs.recommendations,
          ...skillRecs.recommendations
        },
        lastFetched: new Date()
      };

      setDataCache(cacheData);
      setSkillGapAnalysis(careerAnalysis.analysis);
      setRecommendations(careerRecs.recommendations);

      if (plansResponse.success && plansResponse.plans?.length > 0) {
        setDevelopmentPlans(plansResponse.plans);
        const sortedPlans = [...plansResponse.plans].sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setActivePlanId(sortedPlans[0].id || sortedPlans[0]._id);
      }

    } catch (error) {
      console.error("Error initializing data:", error);
      setError(error.message || "Failed to load skill development data");
    } finally {
      setIsInitializing(false);
    }
  };

  const handleRefreshData = async () => {
    await initializeAllData();
  };

  const handleAnalysisComplete = (analysis) => {
    setSkillGapAnalysis(analysis);
    // Update cache
    setDataCache(prev => ({
      ...prev,
      careerAnalysis: analysis,
      lastFetched: new Date()
    }));
  };

  const handleRecommendationsLoaded = (recs) => {
    setRecommendations(recs);
    // Update cache
    setDataCache(prev => ({
      ...prev,
      careerRecommendations: recs,
      lastFetched: new Date()
    }));
  };

  const handleStartTraining = (skillGaps, resources) => {
    setSelectedSkillGaps(skillGaps);
    setSelectedResources(resources);
    setShowCreatePlanModal(true);
  };

  const handleCreateDevelopmentPlan = async () => {
    if (!employeeId || selectedSkillGaps.length === 0) return;

    setIsCreatingPlan(true);
    setCreatePlanError("");

    try {
      // Calculate a deadline (3 months from now)
      const deadline = new Date();
      deadline.setMonth(deadline.getMonth() + 3);

      const response = await recommendationService.createDevelopmentPlan(
        employeeId,
        selectedSkillGaps,
        selectedResources,
        deadline.toISOString()
      );

      if (response.success) {
        setShowCreatePlanModal(false);
        setSelectedSkillGaps([]);
        setSelectedResources({});

        // Refresh development plans
        const plansResponse = await recommendationService.getEmployeeDevelopmentPlans(employeeId);
        if (plansResponse.success) {
          setDevelopmentPlans(plansResponse.plans || []);
          setActivePlanId(response.plan_id);
          setActiveTab("tracker");
        }
      } else {
        setCreatePlanError(
          response.message || "Failed to create development plan"
        );
      }
    } catch (error) {
      console.error("Error creating development plan:", error);
      setCreatePlanError(
        "An error occurred while creating the development plan"
      );
    } finally {
      setIsCreatingPlan(false);
    }
  };

  const renderTabContent = () => {
    if (!employeeId) {
      return (
        <Card>
          <div className="py-12 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <p className="text-gray-500 mb-4">Please select an employee to view skill development options</p>
            <Button
              variant="primary"
              onClick={() => navigate("/talent-pool")}
            >
              Browse Employees
            </Button>
          </div>
        </Card>
      );
    }

    switch (activeTab) {
      case "analysis":
        return (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <SkillGapAnalyzer
              employeeId={employeeId}
              employeeData={employee}
              onAnalysisComplete={handleAnalysisComplete}
              initialAnalysis={dataCache.careerAnalysis}
              forceRefresh={false}
            />
            <RecommendationList
              employeeId={employeeId}
              employeeData={employee}
              analysis={skillGapAnalysis || dataCache.careerAnalysis}
              onRecommendationsLoaded={handleRecommendationsLoaded}
              initialRecommendations={dataCache.careerRecommendations}
              forceRefresh={false}
            />
          </div>
        );

      case "resources":
        return recommendations || dataCache.careerRecommendations ? (
          <TrainingResourceList
            employeeId={employeeId}
            recommendations={recommendations || dataCache.careerRecommendations}
            onStartTraining={handleStartTraining}
          />
        ) : (
          <Card>
            <div className="py-8 text-center text-gray-500">
              Please complete skill gap analysis first to see training resources.
            </div>
          </Card>
        );

      case "tracker":
        return developmentPlans.length > 0 ? (
          <div className="space-y-6">
            {developmentPlans.length > 1 && (
              <div className="p-4 bg-white rounded-lg shadow">
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  Select Development Plan
                </label>
                <select
                  value={activePlanId || ""}
                  onChange={(e) => setActivePlanId(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {developmentPlans.map((plan) => (
                    <option key={plan.id || plan._id} value={plan.id || plan._id}>
                      {plan.title ||
                        `Plan created on ${new Date(
                          plan.created_at
                        ).toLocaleDateString()}`}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {activePlanId ? (
              <DevelopmentTracker
                employeeId={employeeId}
                planId={activePlanId}
              />
            ) : (
              <Card>
                <div className="py-8 text-center text-gray-500">
                  Select a development plan to track
                </div>
              </Card>
            )}
          </div>
        ) : (
          <Card>
            <div className="py-8 text-center">
              <p className="mb-4 text-gray-500">
                No development plans found. Create one from skill
                recommendations.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab("analysis")}
              >
                Go to Skill Analysis
              </Button>
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  const renderSkillGapsPreview = () => {
    if (!selectedSkillGaps || selectedSkillGaps.length === 0) return null;

    return (
      <div className="space-y-3">
        {selectedSkillGaps.map((skill, idx) => {
          const skillName = typeof skill === 'string' ? skill : skill.name || skill;
          const resources = selectedResources[skillName] || [];

          return (
            <div key={idx} className="pt-3 border-t">
              <h4 className="font-medium text-gray-800">{skillName}</h4>

              {resources.length > 0 ? (
                <ul className="mt-2 list-disc list-inside">
                  {resources.map((resource, resIdx) => (
                    <li key={resIdx} className="text-sm text-gray-600">
                      {resource.name} ({resource.type || 'Resource'})
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-gray-500">
                  No resources selected for this skill
                </p>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // Show initialization loading screen only when employeeId is present
  if (isInitializing && employeeId) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="mb-6">
              <svg className="w-16 h-16 mx-auto text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Preparing Your Skill Development Journey
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {initializationMessage}
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container px-4 py-6 mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-wrap items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Skill Development
            </h1>
            <p className="text-gray-600">
              {employeeId ? "Analyze skill gaps and create personalized development plans" : "Select an employee to begin"}
            </p>
          </div>

          <div className="flex mt-4 space-x-3 md:mt-0">
            {employeeId && (
              <Button
                variant="outline"
                onClick={handleRefreshData}
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
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                }
              >
                Refresh Data
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => navigate("/talent-pool")}
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
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              }
            >
              Back to Talent Pool
            </Button>
          </div>
        </div>

        {/* Last updated indicator */}
        {dataCache.lastFetched && employeeId && (
          <p className="mt-2 text-xs text-gray-500">
            Last updated: {new Date(dataCache.lastFetched).toLocaleString()}
          </p>
        )}
      </div>

      {error && employeeId ? (
        <div className="p-4 mb-6 text-red-700 rounded-md bg-red-50">
          <p>{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={initializeAllData}
          >
            Retry
          </Button>
        </div>
      ) : employee && employeeId ? (
        <>
          {/* Employee Info */}
          <div className="p-6 mb-6 bg-white rounded-lg shadow">
            <div className="flex flex-wrap md:flex-nowrap">
              <div className="w-full mb-4 md:w-auto md:mb-0 md:mr-6">
                <div className="flex items-center justify-center w-20 h-20 text-2xl font-semibold text-blue-600 bg-blue-100 rounded-full">
                  {employee.Name?.charAt(0) || "U"}
                </div>
              </div>

              <div className="flex-grow">
                <div className="flex flex-wrap items-start justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      {employee.Name || "Unknown"}
                    </h2>
                    <p className="text-gray-600">
                      {employee["Contact Information"]?.Email ||
                        "No email available"}
                    </p>

                    <div className="flex items-center mt-2">
                      <span className="text-xs px-2.5 py-0.5 rounded bg-blue-100 text-blue-800 mr-2">
                        {employee.Experience?.[0]?.Role || "Unknown Role"}
                      </span>
                      <span className="text-xs text-gray-500">
                        {employee.Experience?.[0]?.Company || ""}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 md:mt-0">
                    <div className="text-sm text-gray-600">
                      <div className="flex items-center mb-1">
                        <svg
                          className="w-4 h-4 mr-1 text-gray-400"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                        <span>
                          {employee.Experience?.length || 0} positions
                        </span>
                      </div>

                      <div className="flex items-center mb-1">
                        <svg
                          className="w-4 h-4 mr-1 text-gray-400"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                          />
                        </svg>
                        <span>{employee.Education?.length || 0} degrees</span>
                      </div>

                      <div className="flex items-center">
                        <svg
                          className="w-4 h-4 mr-1 text-gray-400"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                          />
                        </svg>
                        <span>{employee.Skills?.length || 0} skills</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="flex flex-wrap gap-2">
                    {employee.Skills?.slice(0, 8).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs text-gray-800 bg-gray-100 rounded"
                      >
                        {skill}
                      </span>
                    ))}
                    {employee.Skills?.length > 8 && (
                      <span className="px-2 py-1 text-xs text-gray-800 bg-gray-100 rounded">
                        +{employee.Skills.length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="mb-6 overflow-hidden bg-white rounded-lg shadow">
            <div className="border-b">
              <nav className="flex flex-wrap">
                <button
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === "analysis"
                      ? "text-blue-600 border-b-2 border-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setActiveTab("analysis")}
                >
                  Skill Gap Analysis
                </button>
                <button
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === "resources"
                      ? "text-blue-600 border-b-2 border-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setActiveTab("resources")}
                >
                  Training Resources
                </button>
                <button
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === "tracker"
                      ? "text-blue-600 border-b-2 border-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setActiveTab("tracker")}
                >
                  Development Tracker
                </button>
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          {renderTabContent()}
        </>
      ) : (
        !employeeId && renderTabContent()
      )}

      {/* Create Development Plan Modal */}
      <Modal
        isOpen={showCreatePlanModal}
        onClose={() => setShowCreatePlanModal(false)}
        title="Create Development Plan"
        footer={
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowCreatePlanModal(false)}
              disabled={isCreatingPlan}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateDevelopmentPlan}
              disabled={isCreatingPlan || selectedSkillGaps.length === 0}
              icon={
                isCreatingPlan ? (
                  <svg
                    className="w-4 h-4 mr-2 -ml-1 text-white animate-spin"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : null
              }
            >
              {isCreatingPlan ? "Creating..." : "Create Plan"}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            You are about to create a personalized development plan for{" "}
            {employee?.Name || "this employee"} with the following skills and
            resources:
          </p>

          {renderSkillGapsPreview()}

          <div className="mt-4">
            <p className="text-sm text-gray-600">
              This will create a 3-month development plan starting today. You
              will be able to track progress in the Development Tracker tab.
            </p>
          </div>

          {createPlanError && (
            <div className="p-3 text-red-700 rounded-md bg-red-50">
              <p>{createPlanError}</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default SkillDevelopmentPage;