import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import KPIGenerator from "../components/kpi-management/KPIGenerator";
import KPIDashboard from "../components/kpi-management/KPIDashboard";
import GanttChartView from "../components/kpi-management/GanttChartView";
import BurndownChartView from "../components/kpi-management/BurndownChartView";
import KPIAdjuster from "../components/kpi-management/KPIAdjuster";
import KPIRadarChart from "../components/kpi-management/KPIRadarChart";
import KPIProgressTracker from "../components/kpi-management/KPIProgressTracker";
import TeamKPIDashboard from "../components/kpi-management/TeamKPIDashboard";
import TeamAnalysisDashboard from "../components/kpi-management/TeamAnalysisDashboard"; // Add this import
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Loading from "../components/common/Loading";
import Modal from "../components/common/Modal";
import { projectService } from "../services/projectService";
import { kpiService } from "../services/kpiService";
import { useLocation } from "react-router-dom";
import EmployeeAssignmentCard from "../components/talent-pool/EmployeeAssignmentCard";

const KPIManagementPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [project, setProject] = useState(null);
  const [kpis, setKPIs] = useState(null);
  const [ganttData, setGanttData] = useState([]);
  const [employeeCriteria, setEmployeeCriteria] = useState([]);
  const [sprintBreakdown, setSprintBreakdown] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [activeTab, setActiveTab] = useState(
    location.state?.activeTab || "dashboard"
  );
  const [chartPaths, setChartPaths] = useState({});
  const [kpiRecommendations, setKpiRecommendations] = useState([]);

  // Fetch project and KPIs on component mount
  useEffect(() => {
    if (projectId) {
      fetchProjectData();
    }
  }, [projectId]);

  const fetchProjectData = async () => {
    setIsLoading(true);
    setError("");

    try {
      // Fetch project details
      const projectResponse = await projectService.getProject(projectId);

      if (!projectResponse.success) {
        setError(projectResponse.message || "Failed to fetch project data");
        setIsLoading(false);
        return;
      }

      setProject(projectResponse.data);

      // If project has KPIs, fetch them
      if (projectResponse.data.kpi_id) {
        const kpiResponse = await kpiService.getProjectKPIs(projectId);

        if (kpiResponse.success) {
          setKPIs(kpiResponse.data.kpis);
          setGanttData(kpiResponse.data.gantt_chart_data || []);
          setEmployeeCriteria(kpiResponse.data.employee_criteria || []);
          setSprintBreakdown(kpiResponse.data.sprint_breakdown || {});

          // Set chart paths if available
          if (kpiResponse.data.charts) {
            setChartPaths(kpiResponse.data.charts);
          }

          // Fetch KPI recommendations
          fetchKPIRecommendations();
        } else {
          setError(kpiResponse.message || "Failed to fetch KPI data");
        }
      }
    } catch (error) {
      console.error("Error fetching project data:", error);
      setError("An error occurred while fetching project data");
    } finally {
      setIsLoading(false);
    }
  };

  // Add in useEffect to handle location state changes
  useEffect(() => {
    if (location.state?.activeTab) {
      setActiveTab(location.state.activeTab);
    }
  }, [location.state]);

  // In the fetchKPIRecommendations function
  const fetchKPIRecommendations = async () => {
    try {
      const recommendationsResponse =
        await kpiService.generateKPIRecommendations(projectId);
      if (recommendationsResponse.success) {
        setKpiRecommendations(recommendationsResponse.recommendations || []);
      } else {
        // If the endpoint doesn't exist or returns an error, just set empty recommendations
        setKpiRecommendations([]);
        console.log("KPI recommendations not available");
      }
    } catch (error) {
      console.error("Error fetching KPI recommendations:", error);
      // Set empty recommendations array to prevent errors
      setKpiRecommendations([]);
    }
  };

  const handleKPIsGenerated = (data) => {
    setKPIs(data.kpis);
    setGanttData(data.gantt_chart_data || []);
    setEmployeeCriteria(data.employee_criteria || []);
    setSprintBreakdown(data.sprint_breakdown || {});

    // Save KPIs to project
    saveKPIsToProject(data);
  };

  const handleRemoveAssignment = async (roleId) => {
    if (!projectId || !project) return;

    try {
      setIsLoading(true);
      setError("");

      // Get current team data
      const teamData = project.team || {};
      const roleAssignments = teamData.role_assignments || [];

      // Filter out the assignment we want to remove
      const updatedAssignments = roleAssignments.filter(
        (assignment) => assignment.roleId !== roleId.toString()
      );

      // Update the project with the new role assignments
      const response = await projectService.updateProject(projectId, {
        team: {
          ...teamData,
          role_assignments: updatedAssignments,
          updated_at: new Date().toISOString(),
        },
      });

      if (response.success) {
        // Refresh project data to see the changes
        fetchProjectData();
      } else {
        setError(response.message || "Failed to remove team member");
      }
    } catch (error) {
      console.error("Error removing team member:", error);
      setError("An error occurred while removing the team member");
    } finally {
      setIsLoading(false);
    }
  };

  const saveKPIsToProject = async (kpiData) => {
    try {
      const response = await kpiService.createProjectKPIs(projectId, {
        ...kpiData,
        project_details: {
          project_type: project.project_type,
          project_team_size: project.project_team_size,
          project_timeline: project.project_timeline,
          project_languages: project.project_languages,
          project_sprints: project.project_sprints,
        },
      });

      if (response.success) {
        // Set chart paths if returned
        if (response.data && response.data.charts) {
          setChartPaths(response.data.charts);
        }

        // Refresh project data to get updated KPI ID
        fetchProjectData();
      } else {
        console.error("Failed to save KPIs to project:", response.message);
      }
    } catch (error) {
      console.error("Error saving KPIs to project:", error);
    }
  };

  const handleKPIsAdjusted = (adjustedKPIs) => {
    setKPIs(adjustedKPIs);
    setShowAdjustModal(false);
  };

  const handleRegenerateKPIs = () => {
    if (
      window.confirm(
        "Are you sure you want to regenerate KPIs? This will replace all existing KPI data."
      )
    ) {
      setKPIs(null);
      setGanttData([]);
      setEmployeeCriteria([]);
      setSprintBreakdown({});
      setChartPaths({});
    }
  };

  const handleExportReport = async () => {
    try {
      setIsLoading(true);
      const response = await kpiService.exportKPIReport(projectId);
      if (!response.success) {
        setError("Failed to export KPI report. Please try again.");
      }
    } catch (error) {
      console.error("Error exporting report:", error);
      setError("An error occurred while exporting the report");
    } finally {
      setIsLoading(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <KPIDashboard
            kpis={kpis}
            onAdjustKPIs={() => setShowAdjustModal(true)}
          />
        );

      case "radar":
        return <KPIRadarChart kpis={kpis} />;

      case "gantt":
        return (
          <GanttChartView
            chartData={ganttData}
            projectTimeline={project?.project_timeline || 90}
          />
        );

      case "teamanalysis":
      return (
        <TeamAnalysisDashboard
          projectId={projectId}
          projectData={project}
          teamData={project?.team}
        />
      );

      case "teamkpis":
        return (
        <TeamKPIDashboard projectId={projectId} projectKPIs={kpis} />
        );

      case "burndown":
        return (
          <BurndownChartView
            projectTimeline={project?.project_timeline || 90}
            sprints={project?.project_sprints || 5}
            projectId={projectId}
          />
        );

      case "progress":
        return (
          <KPIProgressTracker
            projectId={projectId}
            kpis={kpis}
            sprintData={Array.from(
              { length: project?.project_sprints || 5 },
              (_, i) => ({
                number: i + 1,
                status: i < 2 ? "completed" : i < 3 ? "in-progress" : "planned",
              })
            )}
          />
        );

      case "team":
        return (
          <Card title="Team Criteria">
            <div className="space-y-6">
              <p className="text-gray-700">
                Based on the project requirements, the following team criteria
                have been generated:
              </p>

              <div className="space-y-4">
                {employeeCriteria.map((criteria, index) => {
                  // Find assigned employee for this role
                  const assignedEmployee =
                    project?.team?.role_assignments?.find(
                      (assignment) => assignment.roleId === index.toString()
                    );

                  return (
                    <div key={index} className="p-4 border rounded-md">
                      <h3 className="mb-2 font-medium text-gray-800">
                        {criteria.role}
                        {assignedEmployee && (
                          <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                            Assigned
                          </span>
                        )}
                      </h3>

                      <div className="mt-2">
                        <h4 className="mb-1 text-sm font-medium text-gray-700">
                          Required Skills:
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {criteria.skills.map((skill, skillIndex) => (
                            <span
                              key={skillIndex}
                              className="px-2 py-1 text-xs text-blue-800 bg-blue-100 rounded"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Show assigned employee if available */}
                      {assignedEmployee && (
                        <div className="p-2 mt-3 rounded bg-gray-50">
                          <h4 className="text-sm font-medium text-gray-700">
                            Assigned Employee:
                          </h4>
                          <div className="mt-1">
                            {/* You need to fetch employee details or display ID until fetched */}
                            <EmployeeAssignmentCard
                              employeeId={assignedEmployee.employeeId}
                              projectId={projectId}
                              roleId={index}
                              onRemove={() => handleRemoveAssignment(index)}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex justify-end mt-4">
                        {!assignedEmployee ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              navigate("/talent-pool", {
                                state: {
                                  skillFilter: criteria.skills.join(", "),
                                  projectId: projectId,
                                  roleId: index,
                                  roleName: criteria.role,
                                  isSelectingForProject: true,
                                },
                              })
                            }
                          >
                            Find Matching Employees
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              navigate("/talent-pool", {
                                state: {
                                  skillFilter: criteria.skills.join(", "),
                                  projectId: projectId,
                                  roleId: index,
                                  roleName: criteria.role,
                                  isSelectingForProject: true,
                                  replaceExisting: true,
                                },
                              })
                            }
                          >
                            Replace Employee
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Card>
        );

      case "sprints":
        return (
          <Card title="Sprint Breakdown">
            <div className="space-y-6">
              <p className="text-gray-700">
                The project has been broken down into the following sprints:
              </p>

              <div className="space-y-4">
                {Object.entries(sprintBreakdown).map(([sprint, tasks]) => (
                  <div key={sprint} className="p-4 border rounded-md">
                    <h3 className="mb-2 font-medium text-gray-800">{sprint}</h3>

                    <ul className="pl-5 space-y-1 list-disc">
                      {tasks.map((task, taskIndex) => (
                        <li key={taskIndex} className="text-sm text-gray-600">
                          {task}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        );

      case "recommendations":
        return (
          <Card title="KPI Improvement Recommendations">
            <div className="space-y-6">
              <p className="text-gray-700">
                Based on current project metrics, here are recommendations to
                improve performance:
              </p>

              {kpiRecommendations.length > 0 ? (
                <div className="space-y-4">
                  {kpiRecommendations.map((recommendation, index) => (
                    <div key={index} className="p-4 border rounded-md">
                      <div className="flex items-start">
                        <div
                          className={`p-2 mr-3 rounded-full ${
                            recommendation.priority === "high"
                              ? "bg-red-100"
                              : recommendation.priority === "medium"
                              ? "bg-yellow-100"
                              : "bg-blue-100"
                          }`}
                        >
                          <svg
                            className="w-5 h-5 text-gray-700"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            ></path>
                          </svg>
                        </div>
                        <div>
                          <h3 className="mb-2 font-medium text-gray-800">
                            {recommendation.title}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {recommendation.description}
                          </p>

                          {recommendation.actionItems &&
                            recommendation.actionItems.length > 0 && (
                              <div className="mt-3">
                                <h4 className="mb-1 text-xs font-medium text-gray-700">
                                  Suggested Actions:
                                </h4>
                                <ul className="pl-5 space-y-1 list-disc">
                                  {recommendation.actionItems.map(
                                    (action, actionIndex) => (
                                      <li
                                        key={actionIndex}
                                        className="text-sm text-gray-600"
                                      >
                                        {action}
                                      </li>
                                    )
                                  )}
                                </ul>
                              </div>
                            )}

                          <div className="flex mt-3">
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${
                                recommendation.priority === "high"
                                  ? "bg-red-100 text-red-800"
                                  : recommendation.priority === "medium"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {recommendation.priority.charAt(0).toUpperCase() +
                                recommendation.priority.slice(1)}{" "}
                              Priority
                            </span>

                            {recommendation.category && (
                              <span className="ml-2 text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-800">
                                {recommendation.category}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center">
                  <p className="text-gray-500">
                    No recommendations available yet. Recommendations will be
                    generated as project data is collected.
                  </p>
                </div>
              )}
            </div>
          </Card>
        );

      default:
        return (
          <KPIDashboard
            kpis={kpis}
            onAdjustKPIs={() => setShowAdjustModal(true)}
          />
        );
    }
  };

  return (
    <div className="container px-4 py-6 mx-auto">
      <div className="mb-6">
        <div className="flex flex-wrap items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {project ? `KPI Management: ${project.name}` : "KPI Management"}
            </h1>
            <p className="text-gray-600">
              Generate and monitor KPIs for your project
            </p>
          </div>

          <div className="flex mt-4 space-x-3 md:mt-0">
            {kpis && (
              <>
                <Button
                  variant="outline"
                  onClick={handleExportReport}
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
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  }
                >
                  Export Report
                </Button>

                <Button
                  variant="outline"
                  onClick={handleRegenerateKPIs}
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
                  Regenerate KPIs
                </Button>
              </>
            )}

            <Button
              variant="outline"
              onClick={() => navigate("/projects")}
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
              Back to Projects
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12">
          <Loading text="Loading project data..." />
        </div>
      ) : error ? (
        <div className="p-4 mb-6 text-red-700 rounded-md bg-red-50">
          <p>{error}</p>
          <div className="mt-4">
            <Button variant="outline" size="sm" onClick={fetchProjectData}>
              Retry
            </Button>
          </div>
        </div>
      ) : (
        <>
          {!kpis ? (
            <KPIGenerator
              projectData={project}
              onKPIsGenerated={handleKPIsGenerated}
            />
          ) : (
            <>
              <div className="mb-6 overflow-hidden bg-white rounded-lg shadow">
                <div className="overflow-x-auto border-b">
                  <nav className="flex flex-nowrap">
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "dashboard"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("dashboard")}
                    >
                      Dashboard
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "progress"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("progress")}
                    >
                      Progress Tracker
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "radar"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("radar")}
                    >
                      Radar Chart
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "gantt"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("gantt")}
                    >
                      Gantt Chart
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "burndown"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("burndown")}
                    >
                      Burndown Chart
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "team"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("team")}
                    >
                      Team Criteria
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "teamkpis"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("teamkpis")}
                    >
                      Team KPIs
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "teamanalysis"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("teamanalysis")}
                    >
                      Team Analysis
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "sprints"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("sprints")}
                    >
                      Sprint Breakdown
                    </button>
                    <button
                      className={`px-6 py-3 text-sm font-medium whitespace-nowrap ${
                        activeTab === "recommendations"
                          ? "text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                      onClick={() => setActiveTab("recommendations")}
                    >
                      Recommendations
                    </button>
                  </nav>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-1 gap-4 mb-6 md:grid-cols-2 lg:grid-cols-4">
                    <div className="p-4 rounded-md bg-gray-50">
                      <h3 className="mb-1 text-sm font-medium text-gray-700">
                        Project Type
                      </h3>
                      <p className="text-lg font-semibold text-gray-900">
                        {project?.project_type || "Unknown"}
                      </p>
                    </div>

                    <div className="p-4 rounded-md bg-gray-50">
                      <h3 className="mb-1 text-sm font-medium text-gray-700">
                        Team Size
                      </h3>
                      <p className="text-lg font-semibold text-gray-900">
                        {project?.project_team_size || "0"} members
                      </p>
                    </div>

                    <div className="p-4 rounded-md bg-gray-50">
                      <h3 className="mb-1 text-sm font-medium text-gray-700">
                        Timeline
                      </h3>
                      <p className="text-lg font-semibold text-gray-900">
                        {project?.project_timeline || "0"} days
                      </p>
                    </div>

                    <div className="p-4 rounded-md bg-gray-50">
                      <h3 className="mb-1 text-sm font-medium text-gray-700">
                        Sprints
                      </h3>
                      <p className="text-lg font-semibold text-gray-900">
                        {project?.project_sprints || "0"} sprints
                      </p>
                    </div>
                  </div>

                  {project?.project_languages && (
                    <div className="mt-2">
                      <h3 className="mb-2 text-sm font-medium text-gray-700">
                        Technologies & Languages
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {Array.isArray(project.project_languages)
                          ? project.project_languages.map((lang, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 text-xs text-gray-800 bg-gray-100 rounded"
                              >
                                {lang}
                              </span>
                            ))
                          : project.project_languages
                              .split(",")
                              .map((lang, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 text-xs text-gray-800 bg-gray-100 rounded"
                                >
                                  {lang.trim()}
                                </span>
                              ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {renderTabContent()}
            </>
          )}
        </>
      )}

      {/* KPI Adjustment Modal */}
      <Modal
        isOpen={showAdjustModal}
        onClose={() => setShowAdjustModal(false)}
        title="Adjust KPIs"
        size="lg"
      >
        <KPIAdjuster
          projectId={projectId}
          kpis={kpis}
          onKPIsAdjusted={handleKPIsAdjusted}
        />
      </Modal>
    </div>
  );
};

export default KPIManagementPage;
