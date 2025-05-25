import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import Modal from "../common/Modal";
import { Link } from "react-router-dom";
import { projectService } from "../../services/projectService";
import { employeeService } from "../../services/employeeService";
import { kpiService } from "../../services/kpiService";

const DeveloperMatcher = ({
  projectId,
  roleCriteria,
  onUpdateTeam,
  onBack,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isMatching, setIsMatching] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [project, setProject] = useState(null);
  const [matchedEmployees, setMatchedEmployees] = useState([]);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [projectKPIs, setProjectKPIs] = useState(null);
  const [showKpiModal, setShowKpiModal] = useState(false);
  const [selectedEmployeeKPIs, setSelectedEmployeeKPIs] = useState(null);
  const [selectedEmployeeName, setSelectedEmployeeName] = useState("");

  useEffect(() => {
    if (projectId) {
      fetchProjectDetails();
    }
  }, [projectId]);

  const fetchProjectDetails = async () => {
    setIsLoading(true);
    setError("");

    try {
      // Fetch project details
      const response = await projectService.getProject(projectId);

      if (response.success) {
        setProject(response.data);

        // If the project already has a team, load these employees as selected
        if (
          response.data.team &&
          response.data.team.employee_ids &&
          response.data.team.employee_ids.length > 0 &&
          !roleCriteria // Only load all team members if not a role-specific match
        ) {
          setSelectedEmployees(response.data.team.employee_ids);
        }

        // If the project has KPIs, fetch them
        if (response.data.kpi_id) {
          const kpiResponse = await kpiService.getProjectKPIs(projectId);
          if (kpiResponse.success) {
            setProjectKPIs(kpiResponse.data.kpis);
          }
        }

        // If we have role criteria, match employees for that role right away
        if (roleCriteria) {
          matchEmployees(roleCriteria);
        }
      } else {
        setError(response.message || "Failed to fetch project details");
      }
    } catch (error) {
      console.error("Error fetching project details:", error);
      setError("An error occurred while fetching project details");
    } finally {
      setIsLoading(false);
    }
  };

  const matchEmployees = async (roleDetails = null) => {
    if (!project) return;

    setIsMatching(true);
    setError("");

    try {
      // Building project criteria
      const projectCriteria = {
        languages: roleDetails?.skills || project.project_languages,
        field: project.project_type,
        people_count: roleDetails ? 10 : project.project_team_size, // Show more candidates when matching for a specific role
        project_type: project.project_type,
      };

      // Different API endpoint for matching with KPIs
      let response;
      if (projectKPIs && roleDetails) {
        response = await employeeService.matchEmployeesWithKPIs({
          project_criteria: projectCriteria,
          project_kpis: projectKPIs,
          role_criteria: roleDetails,
        });
      } else {
        response = await employeeService.matchEmployees({
          project_criteria: projectCriteria,
        });
      }

      if (response.success) {
        setMatchedEmployees(response.matched_employees || []);

        // If we're matching for a specific role, clear any previous selections
        if (roleDetails) {
          setSelectedEmployees([]);
        }
      } else {
        setError(response.message || "Failed to match employees");
      }
    } catch (error) {
      console.error("Error matching employees:", error);
      setError("An error occurred while matching employees");
    } finally {
      setIsMatching(false);
    }
  };

  // Add the new function for finding complementary team members
  const matchWithTeamContext = async () => {
    if (!project) return;

    setIsMatching(true);
    setError("");

    try {
      const response = await employeeService.matchWithTeamContext({
        project_criteria: {
          languages: project.project_languages,
          field: project.project_type,
          people_count: project.project_team_size - selectedEmployees.length,
          project_type: project.project_type,
        },
        existing_team: selectedEmployees,
        project_id: projectId
      });

      if (response.success) {
        setMatchedEmployees(response.matched_employees || []);
      } else {
        setError(response.message || "Failed to find complementary team members");
      }
    } catch (error) {
      console.error("Error matching with team context:", error);
      setError("An error occurred while finding complementary team members");
    } finally {
      setIsMatching(false);
    }
  };

  const toggleEmployeeSelection = (employeeId) => {
    setSelectedEmployees((prev) => {
      if (prev.includes(employeeId)) {
        return prev.filter((id) => id !== employeeId);
      } else {
        // For role-specific assignments, we might want to limit to a single employee per role
        if (roleCriteria) {
          return [employeeId]; // Replace previous selections for role-specific matching
        }
        return [...prev, employeeId];
      }
    });
  };

  const handleAssignTeam = async () => {
    if (!project || selectedEmployees.length === 0) return;

    setIsLoading(true);
    setError("");
    setSuccess(false);

    try {
      // Get current team data
      const currentTeam = project.team || {};

      // Build updated team object
      let updatedTeam = {};

      // If we're assigning for a specific role
      if (roleCriteria) {
        console.log("Assigning for specific role:", roleCriteria.role);
        console.log("Selected employees:", selectedEmployees);

        // Start with existing role assignments or initialize new structure
        let roleAssignments = {};

        // First, check if the project already has a role_assignments field
        if (currentTeam.role_assignments) {
          roleAssignments = { ...currentTeam.role_assignments };
        }
        // Handle the existing legacy format where there's a single role field
        else if (currentTeam.role) {
          // Convert the old format to the new format
          roleAssignments = {
            [currentTeam.role]: currentTeam.employee_ids || [],
          };
        }

        // Update with the newly selected employees for this role
        roleAssignments[roleCriteria.role] = selectedEmployees;

        // Get all employee IDs from all roles
        const allEmployeeIds = new Set();
        Object.values(roleAssignments).forEach((ids) => {
          ids.forEach((id) => allEmployeeIds.add(id));
        });

        updatedTeam = {
          employee_ids: Array.from(allEmployeeIds),
          role_assignments: roleAssignments,
          updated_at: new Date().toISOString(),
        };
      }
      // If we're just assigning the general team (not role-specific)
      else {
        updatedTeam = {
          employee_ids: selectedEmployees,
          updated_at: new Date().toISOString(),
        };

        // Preserve existing role assignments if they exist
        if (currentTeam.role_assignments) {
          updatedTeam.role_assignments = currentTeam.role_assignments;
        }
        // Handle legacy format
        else if (currentTeam.role) {
          updatedTeam.role = currentTeam.role;
          updatedTeam.role_id = currentTeam.role_id;
        }
      }

      console.log("Updating team with:", updatedTeam);

      // Update project with new team structure
      const response = await projectService.updateProject(projectId, {
        team: updatedTeam,
      });

      if (response.success) {
        // Call the parent component's update function if provided
        if (onUpdateTeam) {
          onUpdateTeam(updatedTeam);
        }

        // Show success message
        setSuccess(true);

        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          setSuccess(false);
        }, 3000);

        // Refresh project data
        fetchProjectDetails();
      } else {
        setError(response.message || "Failed to assign team");
      }
    } catch (error) {
      console.error("Error assigning team:", error);
      setError("An error occurred while assigning the team");
    } finally {
      setIsLoading(false);
    }
  };

  const viewEmployeeKPIs = (employee) => {
    if (employee.specialized_kpis) {
      setSelectedEmployeeKPIs(employee.specialized_kpis);
      setSelectedEmployeeName(employee.employee.Name);
      setShowKpiModal(true);
    }
  };

  // Function to render the compatibility score with appropriate color
  const renderCompatibilityScore = (percentage) => {
    let bgColor = "bg-red-100 text-red-800";
    if (percentage >= 80) return "bg-green-100 text-green-800";
    if (percentage >= 60) return "bg-yellow-100 text-yellow-800";
    if (percentage >= 40) return "bg-orange-100 text-orange-800";
    return bgColor;
  };

  // Function to render the match scores with appropriate colors
  const renderMatchScore = (score) => {
    let bgColor = "bg-red-100 text-red-800";
    if (score >= 0.8) return "bg-green-100 text-green-800";
    if (score >= 0.6) return "bg-yellow-100 text-yellow-800";
    if (score >= 0.4) return "bg-orange-100 text-orange-800";
    return bgColor;
  };

  // Function to render the status badge for a KPI
  const renderStatusBadge = (status) => {
    switch (status) {
      case "On Track":
        return (
          <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">
            On Track
          </span>
        );
      case "At Risk":
        return (
          <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded">
            At Risk
          </span>
        );
      case "Below Target":
        return (
          <span className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded">
            Below Target
          </span>
        );
      default:
        return (
          <span className="bg-gray-100 text-gray-800 text-xs px-2 py-0.5 rounded">
            {status}
          </span>
        );
    }
  };

  // Function to render skills with match highlighting
  const renderSkills = (employee) => {
    if (!employee.skill_compatibility) return null;

    const matchedSkills = employee.skill_compatibility.matched_skills || [];
    const missingSkills = employee.skill_compatibility.missing_skills || [];
    const partialMatches = employee.skill_compatibility.partial_matches || {};

    return (
      <div className="mt-3">
        <h5 className="mb-1 text-xs font-medium text-gray-700">Skills:</h5>
        <div className="flex flex-wrap gap-1">
          {/* Matched skills */}
          {matchedSkills.map((skill, index) => (
            <span
              key={`matched-${index}`}
              className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded"
            >
              {skill}
            </span>
          ))}

          {/* Partial match skills */}
          {Object.entries(partialMatches).map(([skill, match], index) => (
            <span
              key={`partial-${index}`}
              className="bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded"
              title={`Partially matched with: ${match.matched_skill}`}
            >
              {skill} ({Math.round(match.similarity * 100)}%)
            </span>
          ))}

          {/* Missing skills */}
          {missingSkills.map((skill, index) => (
            <span
              key={`missing-${index}`}
              className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded opacity-70"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Card
      title={
        roleCriteria
          ? `Match Developers for ${roleCriteria.role}`
          : "Match Developers to Project"
      }
    >
      {isLoading && !matchedEmployees.length ? (
        <div className="py-6">
          <Loading text="Loading project details..." />
        </div>
      ) : error ? (
        <div className="p-4 text-red-700 rounded-md bg-red-50">
          <p>{error}</p>
        </div>
      ) : !project ? (
        <div className="py-6 text-center">
          <p className="text-gray-500">Project not found</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="p-4 rounded-md bg-gray-50">
            <h3 className="mb-2 font-medium text-gray-800">{project.name}</h3>
            <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
              <div>
                <span className="text-gray-600">Project Type:</span>{" "}
                <span className="font-medium">
                  {project.project_type || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Team Size:</span>{" "}
                <span className="font-medium">
                  {project.project_team_size || "N/A"} members
                </span>
              </div>
              <div>
                <span className="text-gray-600">Technologies:</span>{" "}
                <span className="font-medium">
                  {project.project_languages || "N/A"}
                </span>
              </div>
            </div>
          </div>

          {roleCriteria && (
            <div className="p-4 border-l-4 border-blue-500 bg-blue-50">
              <h3 className="font-medium text-blue-800 text-md">
                Role Requirements
              </h3>
              <p className="mt-1 text-sm text-blue-700">
                Selecting a developer for: <strong>{roleCriteria.role}</strong>
              </p>
              <div className="mt-2">
                <span className="text-sm text-blue-700">Required Skills:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {roleCriteria.skills.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-800">
              {matchedEmployees.length > 0
                ? "Matched Developers"
                : "Find Suitable Developers"}
            </h3>
            <div className="flex space-x-2">
              <Button
                onClick={() => matchEmployees(roleCriteria)}
                disabled={isMatching || !project}
                icon={
                  isMatching ? (
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
                  ) : (
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
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  )
                }
              >
                {isMatching
                  ? "Matching..."
                  : matchedEmployees.length > 0
                  ? "Re-match Developers"
                  : "Find Best Matches"}
              </Button>

              {/* Add the complementary team members button */}
              {selectedEmployees.length > 0 && !roleCriteria && (
                <Button
                  variant="outline"
                  onClick={matchWithTeamContext}
                  disabled={isMatching}
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
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                      />
                    </svg>
                  }
                >
                  Find Complementary Members
                </Button>
              )}
            </div>
          </div>

          {isMatching ? (
            <div className="py-6">
              <Loading text="Matching developers to project requirements..." />
            </div>
          ) : matchedEmployees.length === 0 ? (
            <div className="p-8 text-center rounded-md bg-gray-50">
              <svg
                className="w-12 h-12 mx-auto mb-4 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <p className="mb-4 text-gray-500">
                Click "Find Best Matches" to automatically match the most
                suitable developers for this project based on skills and
                experience.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => matchEmployees(roleCriteria)}
              >
                Find Matches
              </Button>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {matchedEmployees.map((matchData) => (
                  <div
                    key={matchData.employee._id}
                    className={`border rounded-lg p-4 transition ${
                      selectedEmployees.includes(matchData.employee._id)
                        ? "border-green-500 bg-green-50"
                        : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between">
                      <div className="flex-grow">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id={`employee-${matchData.employee._id}`}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            checked={selectedEmployees.includes(
                              matchData.employee._id
                            )}
                            onChange={() =>
                              toggleEmployeeSelection(matchData.employee._id)
                            }
                          />
                          <label
                            htmlFor={`employee-${matchData.employee._id}`}
                            className="ml-2 font-medium text-gray-900"
                          >
                            {matchData.employee.Name}
                          </label>
                          <div className="flex items-center ml-3 space-x-2">
                            <span className="text-xs text-gray-500">
                              Compatibility:
                            </span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${renderCompatibilityScore(
                                matchData.compatibility_percentage ||
                                  Math.round(matchData.total_score * 100)
                              )}`}
                            >
                              {Math.round(
                                matchData.compatibility_percentage ||
                                  matchData.total_score * 100
                              )}
                              %
                            </span>
                          </div>
                        </div>

                        <div className="mt-2 ml-6">
                          <div className="text-sm text-gray-600">
                            {matchData.employee["Contact Information"]?.Email ||
                              "No email available"}
                          </div>

                          <div className="grid grid-cols-2 mt-2 text-sm gap-x-6 gap-y-2">
                            <div>
                              <span className="text-gray-500">
                                Skill Match:
                              </span>{" "}
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${renderMatchScore(
                                  matchData.scores.skill_match || 0
                                )}`}
                              >
                                {Math.round(
                                  (matchData.scores.skill_match || 0) * 100
                                )}
                                %
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">
                                Experience Relevance:
                              </span>{" "}
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${renderMatchScore(
                                  matchData.scores.experience_relevance || 0
                                )}`}
                              >
                                {Math.round(
                                  (matchData.scores.experience_relevance || 0) *
                                    100
                                )}
                                %
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">
                                Years of Experience:
                              </span>{" "}
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${renderMatchScore(
                                  matchData.scores.years_experience || 0
                                )}`}
                              >
                                {Math.round(
                                  (matchData.scores.years_experience || 0) * 100
                                )}
                                %
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">
                                Project Type Match:
                              </span>{" "}
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${renderMatchScore(
                                  matchData.scores.project_type_match || 0
                                )}`}
                              >
                                {Math.round(
                                  (matchData.scores.project_type_match || 0) *
                                    100
                                )}
                                %
                              </span>
                            </div>
                          </div>

                          {/* Render skills with highlighting */}
                          {renderSkills(matchData)}

                          {/* Specialized KPIs button */}
                          {matchData.specialized_kpis && (
                            <div className="mt-3">
                              <button
                                onClick={() => viewEmployeeKPIs(matchData)}
                                className="text-sm text-blue-600 underline hover:text-blue-800"
                              >
                                View Specialized KPIs
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="mt-2 md:mt-0">
                        <Link
                          to={`/talent-pool/${matchData.employee._id}`}
                          className="flex items-center text-sm text-blue-600 hover:text-blue-800 whitespace-nowrap"
                        >
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
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                          View Profile
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {success && (
                <div className="p-3 text-green-700 rounded-md bg-green-50">
                  <p>
                    {roleCriteria
                      ? `Developer successfully assigned to ${roleCriteria.role} role!`
                      : "Team assigned successfully! Team members have been updated."}
                  </p>
                </div>
              )}

              <div className="flex items-center justify-between pt-6 border-t">
                <div className="text-sm text-gray-500">
                  Selected {selectedEmployees.length} of{" "}
                  {matchedEmployees.length} developers
                </div>
                <div className="flex space-x-3">
                  {onBack && (
                    <Button
                      variant="outline"
                      onClick={onBack}
                      disabled={isLoading}
                    >
                      Back
                    </Button>
                  )}
                  <Button
                    onClick={handleAssignTeam}
                    disabled={selectedEmployees.length === 0 || isLoading}
                    icon={
                      isLoading ? (
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
                      ) : (
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
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      )
                    }
                  >
                    {isLoading
                      ? "Assigning..."
                      : roleCriteria
                      ? `Assign to ${roleCriteria.role} Role`
                      : "Assign Team"}
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Employee KPIs Modal */}
      <Modal
        isOpen={showKpiModal}
        onClose={() => setShowKpiModal(false)}
        title={`Specialized KPIs for ${selectedEmployeeName}`}
        size="lg"
      >
        <div className="space-y-6">
          <p className="text-sm text-gray-600">
            These KPIs are tailored specifically for {selectedEmployeeName}{" "}
            based on their skills and the role requirements.
          </p>

          {selectedEmployeeKPIs &&
            Object.entries(selectedEmployeeKPIs).map(([category, kpis]) => (
              <div key={category} className="space-y-3">
                <h3 className="font-medium text-gray-800 capitalize text-md">
                  {category.replace("_", " ")}
                </h3>

                <div className="space-y-2">
                  {Object.entries(kpis).map(([kpiName, kpiData]) => (
                    <div key={kpiName} className="p-3 border rounded-md">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium text-gray-700 capitalize">
                          {kpiName.replace(/_/g, " ")}
                        </h4>
                        {renderStatusBadge(kpiData.status)}
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div className="text-sm">
                          <span className="text-gray-500">Current:</span>{" "}
                          {kpiData.value}
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-500">Target:</span>{" "}
                          {kpiData.target}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

          <div className="flex justify-end">
            <Button variant="primary" onClick={() => setShowKpiModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

export default DeveloperMatcher;