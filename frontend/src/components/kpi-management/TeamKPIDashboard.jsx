import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import Modal from "../common/Modal";
import { projectService } from "../../services/projectService";
import { employeeService } from "../../services/employeeService";
import { kpiService } from "../../services/kpiService";
import IndividualKPITracker from "./IndividualKPITracker";
import KPIComparisonChart from "./KPIComparisonChart";

const TeamKPIDashboard = ({ projectId, projectKPIs }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [teamData, setTeamData] = useState(null);
  const [employeeDetails, setEmployeeDetails] = useState([]);
  const [specializedKPIs, setSpecializedKPIs] = useState({});
  const [selectedEmployeeKPIs, setSelectedEmployeeKPIs] = useState(null);
  const [selectedEmployeeName, setSelectedEmployeeName] = useState("");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [showKpiModal, setShowKpiModal] = useState(false);
  const [activeTab, setActiveTab] = useState("details");
  const [kpiData, setKpiData] = useState(null);
  const [debugInfo, setDebugInfo] = useState({});

  useEffect(() => {
    if (projectId) {
      fetchTeamData();
    }
  }, [projectId]);

  const fetchTeamData = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      console.log("Fetching team data for project:", projectId);
      
      // First get the KPI data to access role criteria
      const kpiResponse = await kpiService.getProjectKPIs(projectId);
      console.log("KPI response:", kpiResponse);
      
      if (!kpiResponse.success) {
        throw new Error("Failed to fetch KPI data: " + (kpiResponse.message || "Unknown error"));
      }
      
      setKpiData(kpiResponse.data);

      // Then get team data
      const response = await projectService.getProjectTeam(projectId);
      console.log("Team data response:", response);

      if (!response.success) {
        throw new Error("Failed to fetch team data: " + (response.message || "Unknown error"));
      }
      
      setTeamData(response.data);
      setDebugInfo(prev => ({...prev, teamData: response.data}));

      // Extract employee IDs from all possible sources
      const employeeIds = [];
      
      // Get from role_assignments if it's an array
      if (response.data.role_assignments && Array.isArray(response.data.role_assignments)) {
        response.data.role_assignments.forEach(assignment => {
          if (assignment.employeeId && !employeeIds.includes(assignment.employeeId)) {
            employeeIds.push(assignment.employeeId);
          }
        });
      } 
      // Get from role_assignments if it's an object
      else if (response.data.role_assignments && typeof response.data.role_assignments === 'object') {
        Object.entries(response.data.role_assignments).forEach(([roleId, employeeId]) => {
          if (employeeId && !employeeIds.includes(employeeId)) {
            employeeIds.push(employeeId);
          }
        });
      }
      
      // Also include employee_ids array if present
      if (response.data.employee_ids && Array.isArray(response.data.employee_ids)) {
        response.data.employee_ids.forEach(id => {
          if (!employeeIds.includes(id)) {
            employeeIds.push(id);
          }
        });
      }

      console.log("Extracted employee IDs:", employeeIds);
      setDebugInfo(prev => ({...prev, employeeIds}));

      // Fetch employee details if there are IDs
      if (employeeIds.length > 0) {
        await fetchEmployeeDetails(employeeIds);
        await fetchSpecializedKPIs(employeeIds, kpiResponse.data);
      } else {
        setEmployeeDetails([]);
        setSpecializedKPIs({});
        console.log("No employee IDs found in team data");
      }
    } catch (error) {
      console.error("Error fetching team data:", error);
      setError("An error occurred while fetching team data: " + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchEmployeeDetails = async (employeeIds) => {
    try {
      console.log("Fetching details for employees:", employeeIds);
      
      // Map each ID to a promise that fetches the employee details
      const employeePromises = employeeIds.map((id) => 
        employeeService.getEmployee(id)
      );

      // Wait for all promises to resolve
      const employeeResponses = await Promise.all(employeePromises);
      console.log("Employee responses:", employeeResponses);

      // Extract employee data from successful responses
      const employees = employeeResponses
        .filter((response) => response.success)
        .map((response) => response.data);
      
      console.log("Processed employee details:", employees);
      setEmployeeDetails(employees);
      setDebugInfo(prev => ({...prev, employeeDetails: employees}));
    } catch (error) {
      console.error("Error fetching employee details:", error);
      setError("An error occurred while fetching employee details: " + error.message);
    }
  };

  const fetchSpecializedKPIs = async (employeeIds, kpiResponseData) => {
  try {
    console.log("Fetching specialized KPIs for employees:", employeeIds);
    
    if (!kpiResponseData) {
      throw new Error("KPI data not available");
    }

    // Extract role criteria from KPI data
    const roleCriteria = kpiResponseData.employee_criteria || [];
    console.log("Role criteria:", roleCriteria);
    setDebugInfo(prev => ({...prev, roleCriteria}));

    // Map employees to their roles
    const employeeRoleMap = {};

    // Try to get role assignments from team data
    if (teamData) {
      // If role_assignments is an array of objects
      if (teamData.role_assignments && Array.isArray(teamData.role_assignments)) {
        console.log("Processing role assignments as array:", teamData.role_assignments);
        teamData.role_assignments.forEach(assignment => {
          const roleId = parseInt(assignment.roleId, 10);
          if (roleCriteria[roleId]) {
            employeeRoleMap[assignment.employeeId] = {
              ...roleCriteria[roleId],
              roleId: roleId
            };
          }
        });
      } 
      // If role_assignments is an object mapping roleId to employeeId
      else if (teamData.role_assignments && typeof teamData.role_assignments === 'object') {
        console.log("Processing role assignments as object:", teamData.role_assignments);
        Object.entries(teamData.role_assignments).forEach(([roleId, employeeId]) => {
          const roleIdNum = parseInt(roleId, 10);
          if (roleCriteria[roleIdNum]) {
            employeeRoleMap[employeeId] = {
              ...roleCriteria[roleIdNum],
              roleId: roleIdNum
            };
          }
        });
      }
    }

    console.log("Employee-role mapping:", employeeRoleMap);
    setDebugInfo(prev => ({...prev, employeeRoleMap}));

    // If no role assignments found, use a fallback approach
    if (Object.keys(employeeRoleMap).length === 0 && roleCriteria.length > 0) {
      console.log("No role assignments found, using fallback approach");
      // Assign roles based on index
      employeeIds.forEach((id, index) => {
        if (roleCriteria[index % roleCriteria.length]) {
          employeeRoleMap[id] = {
            ...roleCriteria[index % roleCriteria.length],
            roleId: index % roleCriteria.length
          };
        }
      });
    }

    // Get specialized KPIs for each employee
    const specializedKPIsResults = {};
    console.log("Starting individual KPI fetching for each employee");

    // Fetch all employees' data first
    const employeeDataPromises = employeeIds.map(id => employeeService.getEmployee(id));
    const employeeDataResponses = await Promise.all(employeeDataPromises);
    
    const employeeDataMap = {};
    employeeDataResponses.forEach((response, index) => {
      if (response.success) {
        employeeDataMap[employeeIds[index]] = response.data;
      }
    });

    // Now fetch KPIs for each employee with their actual data
    for (const employeeId of employeeIds) {
      try {
        const roleData = employeeRoleMap[employeeId];
        const employeeData = employeeDataMap[employeeId];
        
        if (!roleData || !employeeData) {
          console.log(`Missing data for employee ${employeeId}, skipping`);
          continue;
        }
        
        console.log(`Fetching KPIs for employee ${employeeId} with role:`, roleData);
        
        // Match this specific employee with their role criteria
        const response = await employeeService.matchEmployeesWithKPIs({
          project_criteria: {
            field: kpiResponseData.project_details?.project_type || "Software Development",
            languages: roleData.skills || [],
            people_count: 1,
            project_type: kpiResponseData.project_details?.project_type || "Software Development",
          },
          project_kpis: kpiResponseData.kpis,
          role_criteria: roleData,
        });
        
        console.log(`KPI response for employee ${employeeId}:`, response);

        if (response.success && response.matched_employees && response.matched_employees.length > 0) {
          // Find the matched employee in the response
          const matchedEmployee = response.matched_employees.find(
            matched => matched.employee._id === employeeId || 
                      matched.employee.Name === employeeData.Name
          );
          
          if (matchedEmployee && matchedEmployee.specialized_kpis) {
            specializedKPIsResults[employeeId] = matchedEmployee.specialized_kpis;
            console.log(`KPIs added for employee ${employeeId}:`, matchedEmployee.specialized_kpis);
          } else {
            // If not found by exact match, use the first result
            if (response.matched_employees[0].specialized_kpis) {
              specializedKPIsResults[employeeId] = response.matched_employees[0].specialized_kpis;
              console.log(`KPIs added for employee ${employeeId} (using first match)`);
            }
          }
        } else {
          console.log(`Failed to get KPIs for employee ${employeeId}: ${response.message || 'Unknown error'}`);
          
          // Generate default KPIs as fallback
          if (kpiResponseData.kpis) {
            console.log(`Generating default KPIs for employee ${employeeId}`);
            // Import the IndividualKPIGenerator if available
            try {
              const { IndividualKPIGenerator } = await import('../../modules/kpi_generation/individual_kpi_generator');
              const defaultKPIs = IndividualKPIGenerator.generate_individual_kpis(
                kpiResponseData.kpis,
                roleData,
                employeeData
              );
              specializedKPIsResults[employeeId] = defaultKPIs;
            } catch (importError) {
              // If import fails, use the project KPIs as fallback
              specializedKPIsResults[employeeId] = kpiResponseData.kpis;
              console.log(`Using project KPIs as fallback for employee ${employeeId}`);
            }
          }
        }
      } catch (employeeError) {
        console.error(`Error fetching KPIs for employee ${employeeId}:`, employeeError);
        
        // Use project KPIs as fallback
        if (kpiResponseData.kpis) {
          specializedKPIsResults[employeeId] = kpiResponseData.kpis;
          console.log(`Using project KPIs as fallback for employee ${employeeId} due to error`);
        }
      }
    }

    console.log("Final specialized KPIs result:", specializedKPIsResults);
    console.log("Number of employees with KPIs:", Object.keys(specializedKPIsResults).length);
    
    setSpecializedKPIs(specializedKPIsResults);
    setDebugInfo(prev => ({...prev, specializedKPIs: specializedKPIsResults}));
  } catch (error) {
    console.error("Error fetching specialized KPIs:", error);
    setError("Failed to load specialized KPIs: " + error.message);
  }
};

  const viewEmployeeKPIs = (employeeId, employeeName) => {
    console.log(`Viewing KPIs for employee ${employeeId} (${employeeName})`);
    
    if (specializedKPIs[employeeId]) {
      console.log("KPI data found:", specializedKPIs[employeeId]);
      setSelectedEmployeeKPIs(specializedKPIs[employeeId]);
      setSelectedEmployeeName(employeeName);
      setSelectedEmployeeId(employeeId);
      setActiveTab("details");
      setShowKpiModal(true);
    } else {
      console.error(`No specialized KPIs found for employee ${employeeId}`);
      setError(`No specialized KPIs could be loaded for ${employeeName}. Please try refreshing the page.`);
    }
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
            {status || "Unknown"}
          </span>
        );
    }
  };

  const handleRetry = () => {
    setError("");
    fetchTeamData();
  };

  return (
    <Card title="Team KPI Dashboard">
      {isLoading ? (
        <div className="py-6">
          <Loading text="Loading team KPI data..." />
        </div>
      ) : error ? (
        <div className="p-4 text-red-700 rounded-md bg-red-50">
          <p>{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={handleRetry}
          >
            Retry
          </Button>
        </div>
      ) : employeeDetails.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-gray-500">
            No team members assigned to this project yet.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <p className="text-gray-600">
            Each team member has personalized KPIs based on their role and
            skills. Click on "View KPIs" to see detailed metrics for each team
            member.
          </p>

          {/* Debug info in development mode */}
          {process.env.NODE_ENV === 'development' && (
            <div className="p-2 mb-4 text-xs bg-gray-100 rounded">
              <details>
                <summary className="font-bold">Debug Information</summary>
                <div className="mt-2 overflow-auto max-h-40">
                  <p>Team Data Loaded: {teamData ? 'Yes' : 'No'}</p>
                  <p>Employees Loaded: {employeeDetails.length}</p>
                  <p>KPI Data Loaded: {kpiData ? 'Yes' : 'No'}</p>
                  <p>Employee IDs in Debug: {debugInfo.employeeIds?.length || 0}</p>
                  <p>Specialized KPIs Loaded: {Object.keys(specializedKPIs).length}</p>
                </div>
              </details>
            </div>
          )}

          <div className="space-y-4">
            {employeeDetails.map((employee) => (
              <div
                key={employee._id}
                className="p-4 border rounded-md hover:bg-gray-50"
              >
                <div className="flex flex-wrap items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-800">
                      {employee.Name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {employee.Experience?.[0]?.Role || "Unknown Position"}
                    </p>
                    
                    {/* Display assigned role if available - handle both array and object formats */}
                    {teamData?.role_assignments && (
                      <>
                        {/* For array format */}
                        {Array.isArray(teamData.role_assignments) && 
                          teamData.role_assignments
                            .filter(assignment => assignment.employeeId === employee._id)
                            .map((assignment) => (
                              <span
                                key={assignment.roleId}
                                className="mt-1 text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded inline-block mr-1"
                              >
                                {assignment.roleName || `Role ${assignment.roleId}`}
                              </span>
                            ))
                        }
                        
                        {/* For object format */}
                        {!Array.isArray(teamData.role_assignments) && 
                          Object.entries(teamData.role_assignments)
                            .filter(([_, empId]) => empId === employee._id)
                            .map(([roleId]) => {
                              const roleName = kpiData?.employee_criteria?.[parseInt(roleId, 10)]?.role || `Role ${roleId}`;
                              return (
                                <span
                                  key={roleId}
                                  className="mt-1 text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded inline-block mr-1"
                                >
                                  {roleName}
                                </span>
                              );
                            })
                        }
                      </>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        viewEmployeeKPIs(employee._id, employee.Name)
                      }
                      disabled={!specializedKPIs[employee._id]}
                    >
                      {specializedKPIs[employee._id] ? "View KPIs" : "Loading KPIs..."}
                    </Button>
                  </div>
                </div>

                {/* KPI Summary */}
                {specializedKPIs[employee._id] && (
                  <div className="grid grid-cols-2 gap-3 mt-4 md:grid-cols-4">
                    {Object.entries(specializedKPIs[employee._id]).map(
                      ([category, kpis]) => {
                        const totalKPIs = Object.keys(kpis).length;
                        const onTrackCount = Object.values(kpis).filter(
                          (kpi) => kpi.status === "On Track"
                        ).length;

                        const percentage = totalKPIs > 0 
                          ? Math.round((onTrackCount / totalKPIs) * 100)
                          : 0;
                          
                        let statusColor = "bg-red-100 text-red-800";
                        if (percentage >= 75)
                          statusColor = "bg-green-100 text-green-800";
                        else if (percentage >= 50)
                          statusColor = "bg-yellow-100 text-yellow-800";

                        return (
                          <div
                            key={category}
                            className="p-2 rounded bg-gray-50"
                          >
                            <h4 className="text-xs font-medium text-gray-700 capitalize">
                              {category.replace(/_/g, " ")}
                            </h4>
                            <div className="flex items-center justify-between mt-1">
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${statusColor}`}
                              >
                                {percentage}%
                              </span>
                              <span className="text-xs text-gray-500">
                                {onTrackCount}/{totalKPIs} on track
                              </span>
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Employee KPIs Modal */}
      {showKpiModal && selectedEmployeeKPIs && (
        <Modal
          isOpen={showKpiModal}
          onClose={() => setShowKpiModal(false)}
          title={`Specialized KPIs for ${selectedEmployeeName}`}
          size="lg"
        >
          <div className="space-y-6">
            <p className="text-sm text-gray-600">
              These KPIs are tailored specifically for {selectedEmployeeName}{" "}
              based on their skills and assigned role requirements.
            </p>

            {/* Add tabs for different views */}
            <div className="flex mb-4 border-b">
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeTab === "details"
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("details")}
              >
                KPI Details
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeTab === "progress"
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("progress")}
              >
                Track Progress
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeTab === "comparison"
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("comparison")}
              >
                Compare to Project
              </button>
            </div>

            {activeTab === "details" && (
              <div>
                {Object.entries(selectedEmployeeKPIs).map(([category, kpis]) => (
                  <div key={category} className="mb-6 space-y-3">
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
              </div>
            )}

            {activeTab === "progress" && (
              <IndividualKPITracker
                employeeId={selectedEmployeeId}
                employeeName={selectedEmployeeName}
                employeeKPIs={selectedEmployeeKPIs}
                onUpdateProgress={(id, data) =>
                  kpiService.updateIndividualKPIProgress(projectId, id, data)
                }
              />
            )}

            {activeTab === "comparison" && projectKPIs && (
              <KPIComparisonChart
                projectKPIs={projectKPIs}
                employeeKPIs={selectedEmployeeKPIs}
                employeeName={selectedEmployeeName}
              />
            )}

            <div className="flex justify-end">
              <Button variant="primary" onClick={() => setShowKpiModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </Card>
  );
};

export default TeamKPIDashboard;