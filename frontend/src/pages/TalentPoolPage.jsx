import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useEmployee } from "../contexts/EmployeeContext";
import EmployeeList from "../components/talent-pool/EmployeeList";
import EmployeeDetail from "../components/talent-pool/EmployeeDetail";
import EmployeeFilter from "../components/talent-pool/EmployeeFilter";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Loading from "../components/common/Loading";
import { projectService } from "../services/projectService";
import { employeeService } from "../services/employeeService";

const TalentPoolPage = () => {
  const { employeeId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const {
    filteredEmployees,
    employees,
    loading,
    error,
    setFilter,
    clearFilters,
    fetchEmployees,
    fetchEmployeeById,
  } = useEmployee();

  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [viewMode, setViewMode] = useState("list");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [localEmployees, setLocalEmployees] = useState([]);

  // Initialize role assignment data with defaults
  const [roleAssignmentData, setRoleAssignmentData] = useState({
    employeeId: null,
    projectId: null,
    roleId: null,
    roleName: null,
  });

  // Check if we're in selection mode for a project
  const isSelectingForProject = Boolean(location.state?.isSelectingForProject);
  const projectId = location.state?.projectId;
  const roleId = String(location.state?.roleId);
  const roleName = location.state?.roleName;
  const skillFilter = location.state?.skillFilter || "";
  const replaceExisting = location.state?.replaceExisting;

  // This effect runs on component mount to ensure we have employees
  useEffect(() => {
    if (isSelectingForProject && projectId && roleId) {
      console.log("Setting role assignment data from location state:", {
        projectId,
        roleId: String(roleId), // Ensure it's a string
        roleName,
      });

      setRoleAssignmentData({
        employeeId: null, // Will be set when an employee is selected
        projectId: projectId,
        roleId: String(roleId), // Ensure it's a string
        roleName: roleName || "Unknown Role",
      });
    }
  }, [isSelectingForProject, projectId, roleId, roleName]);

  // This effect handles filter changes from location state
  useEffect(() => {
    console.log("Location state changed:", location.state);

    // Force clear all filters first to reset the state
    clearFilters();

    // Then apply the skill filter if provided
    if (skillFilter) {
      console.log("Setting skill filter:", skillFilter);
      setFilter("skills", skillFilter);
    }

    // If we have an employeeId in URL, show the detail view
    if (employeeId) {
      setSelectedEmployeeId(employeeId);
      setViewMode("detail");
    }
  }, [employeeId, skillFilter, setFilter, clearFilters, location.state]);

  // This effect ensures we have employees to display
  useEffect(() => {
    // If there are no filtered employees but we have employees in the store
    // and we're in selection mode, use all employees
    if (
      filteredEmployees.length === 0 &&
      employees.length > 0 &&
      isSelectingForProject
    ) {
      console.log(
        "No filtered employees, but have employees in store:",
        employees.length
      );
      setLocalEmployees(employees);
    } else {
      console.log("Using filtered employees:", filteredEmployees.length);
      setLocalEmployees(filteredEmployees);
    }
  }, [filteredEmployees, employees, isSelectingForProject]);

  // Fetch employee details when selected
  useEffect(() => {
    if (selectedEmployeeId) {
      fetchEmployeeDetails(selectedEmployeeId);
    }
  }, [selectedEmployeeId]);

  // If we need to directly fetch employees (bypassing the context)
  const manuallyFetchEmployees = async () => {
    try {
      setIsLoading(true);
      const response = await employeeService.getAllEmployees();
      if (response.success) {
        console.log("Manually fetched employees:", response.data.length);
        setLocalEmployees(response.data);
      } else {
        setErrorMessage("Failed to load employees");
      }
    } catch (error) {
      console.error("Error fetching employees directly:", error);
      setErrorMessage("Error loading employees");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchEmployeeDetails = async (id) => {
    try {
      setIsLoading(true);
      const employee = await fetchEmployeeById(id);
      setSelectedEmployee(employee);
      setIsLoading(false);
    } catch (error) {
      console.error("Error fetching employee details:", error);
      setErrorMessage("Failed to load employee details");
      setIsLoading(false);
    }
  };

  const handleEmployeeSelect = (employeeId) => {
    console.log("Selected employee ID:", employeeId);

    // Set the selected employee ID
    setSelectedEmployeeId(employeeId);

    // If we're in project role assignment mode, update the roleAssignmentData
    if (isSelectingForProject) {
      console.log("Updating role assignment data with employee:", employeeId);
      console.log("Current projectId:", projectId);
      console.log("Current roleId:", roleId);
      // Find the employee object to get their name for confirmation UI
      const employee =
        employees.find((emp) => emp._id === employeeId) ||
        filteredEmployees.find((emp) => emp._id === employeeId) ||
        localEmployees.find((emp) => emp._id === employeeId);

      console.log("Found employee:", employee?.Name);

      // Update roleAssignmentData with all required fields
      setRoleAssignmentData({
        employeeId: employeeId,
        projectId: projectId,
        roleId: String(roleId), // Ensure it's a string
        roleName: roleName || "Unknown Role",
      });

      console.log("Updated roleAssignmentData:", {
        employeeId: employeeId,
        projectId: projectId,
        roleId: roleId,
        roleName: roleName || "Unknown Role",
      });
    }

    if (viewMode === "list") {
      setViewMode("detail");
    }
  };

  const handleBackToList = () => {
    setSelectedEmployeeId(null);
    setSelectedEmployee(null);
    setViewMode("list");
  };

  const assignEmployeeToRole = async () => {
    // First, log the complete role assignment data
    console.log("Role assignment data before validation:", roleAssignmentData);

    // Then validate each field individually with detailed errors
    if (!roleAssignmentData.employeeId) {
      setErrorMessage("No employee selected. Please select an employee first.");
      return;
    }

    if (!roleAssignmentData.projectId) {
      setErrorMessage(
        "Missing project ID. Please try navigating back to the project and try again."
      );
      return;
    }

    if (!roleAssignmentData.roleId) {
      setErrorMessage(
        "Missing role ID. Please try navigating back to the project and try again."
      );
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      console.log("Assigning employee to role:", roleAssignmentData);

      const response = await projectService.addEmployeeToRole(
        roleAssignmentData.projectId,
        roleAssignmentData.employeeId,
        roleAssignmentData.roleId,
        roleAssignmentData.roleName || "Unknown Role"
      );

      if (response.success) {
        setSuccessMessage("Employee successfully assigned to role");

        // Navigate back to the team page after successful assignment
        setTimeout(() => {
          navigate(`/projects/${roleAssignmentData.projectId}/team`);
        }, 1500);
      } else {
        setErrorMessage(
          response.message || "Failed to assign employee to role"
        );
      }
    } catch (err) {
      console.error("Error assigning employee to role:", err);
      setErrorMessage("An error occurred while assigning the employee");
    } finally {
      setIsLoading(false);
    }
  };
  const cancelSelection = () => {
    if (isSelectingForProject && projectId) {
      navigate(`/projects/${projectId}/team`);
    } else {
      handleBackToList();
    }
  };

  // Add this function to manually retry loading if needed
  const retryLoading = () => {
    fetchEmployees();
    manuallyFetchEmployees();
  };

  const renderContent = () => {
    // If we're loading from context, show loading indicator
    if (loading || isLoading) {
      return <Loading text="Loading employees..." />;
    }

    // Display any errors from the context or component
    if (error || errorMessage) {
      return (
        <div className="p-4 text-red-700 rounded-md bg-red-50">
          <p>{error || errorMessage}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={retryLoading}
          >
            Retry Loading
          </Button>
        </div>
      );
    }

    // If we're showing employee details
    if (viewMode === "detail" && selectedEmployeeId) {
      return (
        <div>
          <EmployeeDetail
            employeeId={selectedEmployeeId}
            employeeData={selectedEmployee}
            onBack={handleBackToList}
          />

          {isSelectingForProject && selectedEmployeeId && (
            <Card className="mt-4">
              <div className="p-4">
                <h3 className="mb-2 text-lg font-medium text-gray-900">
                  Assign to Project Role
                </h3>
                <p className="mb-4 text-gray-600">
                  Assign {selectedEmployee?.Name || "this employee"} to the role
                  of {roleName || "team member"}.
                </p>

                {errorMessage && (
                  <div className="p-3 mb-4 text-red-700 rounded-md bg-red-50">
                    <p>{errorMessage}</p>
                  </div>
                )}

                {successMessage && (
                  <div className="p-3 mb-4 text-green-700 rounded-md bg-green-50">
                    <p>{successMessage}</p>
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <Button
                    variant="outline"
                    onClick={cancelSelection}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={assignEmployeeToRole}
                    disabled={isLoading}
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
                      ) : null
                    }
                  >
                    {isLoading ? "Assigning..." : "Assign to Role"}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      );
    }

    // For employee list view
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <div className="md:col-span-1">
          <EmployeeFilter
            onFilterChange={(filters) => {
              if (filters.search !== undefined)
                setFilter("search", filters.search);
              if (filters.skills !== undefined)
                setFilter("skills", filters.skills);
              if (filters.experienceLevel !== undefined)
                setFilter("experienceLevel", filters.experienceLevel);
            }}
            initialFilters={{ skills: skillFilter }}
          />

          {/* Add a retry button */}
          <Button
            variant="outline"
            size="sm"
            className="w-full mt-4"
            onClick={retryLoading}
          >
            Refresh Employee List
          </Button>
        </div>

        <div className="md:col-span-3">
          <Card>
            {/* Debug info in development mode */}
            {process.env.NODE_ENV === "development" && (
              <div className="p-2 mb-4 text-xs bg-gray-100">
                <p>Debug Info:</p>
                <p>Selected Employee ID: {selectedEmployeeId || "None"}</p>
                <p>Project ID: {projectId || "None"}</p>
                <p>Role ID: {roleId || "None"}</p>
                <p>Role Name: {roleName || "None"}</p>
                <p>
                  Is Selecting For Project:{" "}
                  {isSelectingForProject ? "Yes" : "No"}
                </p>
                <p>Skill Filter: {skillFilter || "None"}</p>
                <p>Employees in Context: {employees?.length || 0}</p>
                <p>Filtered Employees: {filteredEmployees?.length || 0}</p>
                <p>Local Employees: {localEmployees?.length || 0}</p>
                <p>
                  Role Assignment Data: {JSON.stringify(roleAssignmentData)}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between p-3 mb-4 rounded-md bg-blue-50">
              <div>
                <h2 className="text-lg font-medium text-gray-900">
                  {isSelectingForProject
                    ? `Selecting employee for: ${roleName || "Team Member"}`
                    : "Talent Pool"}
                </h2>
                <p className="text-sm text-gray-600">
                  {isSelectingForProject
                    ? "Click on an employee to assign them to this role"
                    : "View and manage your employees"}
                </p>
              </div>

              {isSelectingForProject && (
                <Button variant="outline" onClick={cancelSelection}>
                  Cancel Selection
                </Button>
              )}
            </div>

            {/* If no employees are shown but the context has employees */}
            {localEmployees.length === 0 && employees.length > 0 ? (
              <div className="p-6 text-center">
                <p className="mb-4 text-gray-600">
                  No employees match the current filters. Try adjusting your
                  filters or view all employees.
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    clearFilters();
                    setLocalEmployees(employees);
                  }}
                >
                  Show All Employees
                </Button>
              </div>
            ) : localEmployees.length === 0 ? (
              <div className="p-6 text-center">
                <p className="mb-4 text-gray-600">
                  No employees found. Please add employees through CV upload.
                </p>
                <Button
                  variant="outline"
                  onClick={() => navigate("/cv-upload")}
                >
                  Upload CVs
                </Button>
              </div>
            ) : (
              <EmployeeList
                employees={localEmployees}
                onSelectEmployee={handleEmployeeSelect}
              />
            )}
          </Card>
        </div>
      </div>
    );
  };

  return <div className="container px-4 py-6 mx-auto">{renderContent()}</div>;
};

export default TalentPoolPage;
