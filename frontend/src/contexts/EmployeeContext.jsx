import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
} from "react";
import { employeeService } from "../services/employeeService";
import { cvService } from "../services/cvService";

// Create context
const EmployeeContext = createContext(null);

// Hook for using the employee context
export const useEmployee = () => useContext(EmployeeContext);

export const EmployeeProvider = ({ children }) => {
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [currentEmployee, setCurrentEmployee] = useState(null);
  const [filters, setFilters] = useState({
    search: "",
    skills: "",
    experienceLevel: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all employees
    const fetchEmployees = useCallback(async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await employeeService.getAllEmployees();

        if (response.success) {
          // Ensure all employee IDs are strings
          const employeesWithStringIds = (response.data || []).map(emp => ({
            ...emp,
            _id: String(emp._id || emp.id || ''),
            id: String(emp._id || emp.id || '')
          }));
          
          setEmployees(employeesWithStringIds);
          setFilteredEmployees(employeesWithStringIds);
        } else {
          setError(response.message || "Failed to fetch employees");
        }
      } catch (error) {
        console.error("Error fetching employees:", error);
        setError("An error occurred while fetching employees");
      } finally {
        setLoading(false);
      }
    }, []);

  // Load employees on initial mount
  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  // Apply filters
  useEffect(() => {
    if (!employees.length) return;

    // Apply search filter
    let filtered = [...employees];

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(
        (emp) =>
          (emp.Name && emp.Name.toLowerCase().includes(searchLower)) ||
          (emp["Contact Information"]?.Email &&
            emp["Contact Information"].Email.toLowerCase().includes(
              searchLower
            ))
      );
    }

    // Apply skills filter
    if (filters.skills) {
      const skillsArray = filters.skills
        .split(",")
        .map((skill) => skill.trim().toLowerCase())
        .filter((skill) => skill);

      if (skillsArray.length > 0) {
        filtered = filtered.filter((emp) => {
          if (!emp.Skills || !emp.Skills.length) return false;

          // Changed from .some to .filter to count matching skills
          const matchingSkills = skillsArray.filter((skill) =>
            emp.Skills.some((empSkill) =>
              empSkill.toLowerCase().includes(skill)
            )
          );

          // Show employee if they have at least one of the required skills
          return matchingSkills.length > 0;
        });

        // Add compatibility percentage to each employee
        filtered = filtered.map((emp) => {
          if (!emp.Skills || !emp.Skills.length) {
            emp._compatibility = 0;
            return emp;
          }

          const matchingSkills = skillsArray.filter((skill) =>
            emp.Skills.some((empSkill) =>
              empSkill.toLowerCase().includes(skill)
            )
          );

          emp._compatibility = Math.round(
            (matchingSkills.length / skillsArray.length) * 100
          );
          return emp;
        });

        // Sort by compatibility percentage (highest first)
        filtered.sort(
          (a, b) => (b._compatibility || 0) - (a._compatibility || 0)
        );
      }
    }

    // Apply experience level filter
    if (filters.experienceLevel) {
      filtered = filtered.filter((emp) => {
        // Calculate total years of experience
        let totalYears = 0;
        if (emp.Experience && emp.Experience.length > 0) {
          // Use derived data if available
          totalYears =
            emp._derived?.total_years_experience || emp.Experience.length;
        }

        switch (filters.experienceLevel) {
          case "Junior":
            return totalYears < 2;
          case "Mid-level":
            return totalYears >= 2 && totalYears < 5;
          case "Senior":
            return totalYears >= 5 && totalYears < 8;
          case "Lead":
            return totalYears >= 8;
          default:
            return true;
        }
      });
    }

    setFilteredEmployees(filtered);
  }, [employees, filters]);

  // Fetch employee by ID
  const fetchEmployeeById = useCallback(async (employeeId) => {
    if (!employeeId) return null;

    setLoading(true);
    setError(null);

    try {
      const response = await employeeService.getEmployee(employeeId);

      if (response.success) {
        setCurrentEmployee(response.data);
        return response.data;
      } else {
        setError(response.message || "Failed to fetch employee details");
        return null;
      }
    } catch (error) {
      console.error("Error fetching employee details:", error);
      setError("An error occurred while fetching employee details");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Upload new CV
  const uploadCV = async (formData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await cvService.uploadCV(formData);

      if (response.success) {
        // Refresh employees list
        await fetchEmployees();
        return {
          success: true,
          cvId: response.cv_id,
          data: response.parsed_data,
        };
      } else {
        setError(response.message || "Failed to upload CV");
        return { success: false };
      }
    } catch (error) {
      console.error("Error uploading CV:", error);
      setError("An error occurred while uploading the CV");
      return { success: false };
    } finally {
      setLoading(false);
    }
  };

  // Update employee
  const updateEmployee = async (employeeId, employeeData) => {
    if (!employeeId) return false;

    setLoading(true);
    setError(null);

    try {
      const response = await employeeService.updateEmployee(
        employeeId,
        employeeData
      );

      if (response.success) {
        // Refresh current employee and employees list
        await fetchEmployeeById(employeeId);
        await fetchEmployees();
        return true;
      } else {
        setError(response.message || "Failed to update employee");
        return false;
      }
    } catch (error) {
      console.error("Error updating employee:", error);
      setError("An error occurred while updating the employee");
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Delete employee
  const deleteEmployee = async (employeeId) => {
    if (!employeeId) return false;

    setLoading(true);
    setError(null);

    try {
      const response = await employeeService.deleteEmployee(employeeId);

      if (response.success) {
        // Refresh employees list
        if (currentEmployee && currentEmployee._id === employeeId) {
          setCurrentEmployee(null);
        }
        await fetchEmployees();
        return true;
      } else {
        setError(response.message || "Failed to delete employee");
        return false;
      }
    } catch (error) {
      console.error("Error deleting employee:", error);
      setError("An error occurred while deleting the employee");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getEmployeesForRoleSkills = async (skills) => {
    if (!skills || !skills.length) {
      return employees;
    }

    setLoading(true);

    try {
      // Use the current employees list
      let candidateEmployees = [...employees];

      // If no skills are provided, return all employees
      if (!skills.length) {
        return candidateEmployees;
      }

      // Filter for employees with ANY matching skill (not all)
      // This is more lenient than the normal filter
      const skillsLower = skills.map((s) => s.toLowerCase());

      const filteredForRole = candidateEmployees.filter((emp) => {
        if (!emp.Skills || !emp.Skills.length) return false;

        const empSkillsLower = emp.Skills.map((s) => s.toLowerCase());

        // Return true if ANY skill matches
        return skillsLower.some((skill) =>
          empSkillsLower.some((empSkill) => empSkill.includes(skill))
        );
      });

      return filteredForRole.length > 0 ? filteredForRole : candidateEmployees;
    } catch (error) {
      console.error("Error getting employees for role skills:", error);
      return employees;
    } finally {
      setLoading(false);
    }
  };

  // Set filters
  const setFilter = (filterName, value) => {
    setFilters((prev) => ({
      ...prev,
      [filterName]: value,
    }));
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      search: "",
      skills: "",
      experienceLevel: "",
    });
  };

  const value = {
    employees,
    filteredEmployees,
    currentEmployee,
    filters,
    loading,
    error,
    fetchEmployees,
    fetchEmployeeById,
    uploadCV,
    updateEmployee,
    deleteEmployee,
    setCurrentEmployee,
    setFilter,
    clearFilters,
    getEmployeesForRoleSkills,
  };

  return (
    <EmployeeContext.Provider value={value}>
      {children}
    </EmployeeContext.Provider>
  );
};
