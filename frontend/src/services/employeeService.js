import { api } from './api';
import { extractId } from '../utils/dataHelpers';

// Employee service for handling employee-related API calls
export const employeeService = {
    /**
     * Get all employees
     * @returns {Promise<Object>} - The API response
     */
    getAllEmployees: async () => {
        try {
            const response = await api.get('/employees');
            return response.data;
        } catch (error) {
            console.error('Error getting employees:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get employees',
                data: []
            };
        }
    },

    /**
     * Get a specific employee by ID
     * @param {string|Object} employeeId - The ID of the employee (or employee object)
     * @returns {Promise<Object>} - The API response
     */
    getEmployee: async (employeeId) => {
        try {
            // Ensure we have a valid string ID
            const id = extractId(employeeId);
            
            if (!id) {
                console.error('Invalid employee ID provided:', employeeId);
                return {
                    success: false,
                    message: 'Invalid employee ID'
                };
            }
            
            const response = await api.get(`/employees/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error getting employee:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get employee'
            };
        }
    },

   /**
     * Update an employee's information
     * @param {string|Object} employeeId - The ID of the employee (or employee object)
     * @param {Object} employeeData - The updated employee data
     * @returns {Promise<Object>} - The API response
     */
    updateEmployee: async (employeeId, employeeData) => {
        try {
            const id = extractId(employeeId);
            
            if (!id) {
                console.error('Invalid employee ID provided:', employeeId);
                return {
                    success: false,
                    message: 'Invalid employee ID'
                };
            }
            
            const response = await api.put(`/employees/${id}`, employeeData);
            return response.data;
        } catch (error) {
            console.error('Error updating employee:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to update employee'
            };
        }
    },

    /**
     * Delete an employee
     * @param {string|Object} employeeId - The ID of the employee (or employee object)
     * @returns {Promise<Object>} - The API response
     */
    deleteEmployee: async (employeeId) => {
        try {
            const id = extractId(employeeId);
            
            if (!id) {
                console.error('Invalid employee ID provided:', employeeId);
                return {
                    success: false,
                    message: 'Invalid employee ID'
                };
            }
            
            const response = await api.delete(`/employees/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error deleting employee:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to delete employee'
            };
        }
    },

    /**
     * Get an employee's skills
     * @param {string|Object} employeeId - The ID of the employee (or employee object)
     * @returns {Promise<Object>} - The API response
     */
    getEmployeeSkills: async (employeeId) => {
        try {
            const id = extractId(employeeId);
            
            if (!id) {
                console.error('Invalid employee ID provided:', employeeId);
                return {
                    success: false,
                    message: 'Invalid employee ID'
                };
            }
            
            const response = await api.get(`/employees/${id}/skills`);
            return response.data;
        } catch (error) {
            console.error('Error getting employee skills:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get employee skills'
            };
        }
    },

    /**
     * Get an employee's career path information
     * @param {string|Object} employeeId - The ID of the employee (or employee object)
     * @returns {Promise<Object>} - The API response
     */
    getCareerPath: async (employeeId) => {
        try {
            const id = extractId(employeeId);
            
            if (!id) {
                console.error('Invalid employee ID provided:', employeeId);
                return {
                    success: false,
                    message: 'Invalid employee ID'
                };
            }
            
            const response = await api.get(`/employees/${id}/career-path`);
            return response.data;
        } catch (error) {
            console.error('Error getting career path:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get career path'
            };
        }
    },
    
    /**
     * Match employees to specific project criteria
     * @param {Object} matchData - The matching criteria
     * @returns {Promise<Object>} - The API response
     */
    matchEmployees: async (matchData) => {
        try {
            const response = await api.post('/employees/match', matchData);
            return response.data;
        } catch (error) {
            console.error('Error matching employees:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to match employees',
                matched_employees: []
            };
        }
    },

    /**
     * Filter employees by criteria
     * @param {Object} filterCriteria - The filter criteria
     * @returns {Promise<Object>} - The API response with filtered employees
     */
    filterEmployees: async (filterCriteria) => {
        try {
            // In a real implementation, this would likely be a GET request with query parameters
            // For now, we'll use a simpler approach of fetching all and filtering client-side
            const response = await employeeService.getAllEmployees();

            if (!response.success) {
                return response;
            }

            let filteredEmployees = response.data;

            // Apply filters
            if (filterCriteria) {
                if (filterCriteria.search) {
                    const searchLower = filterCriteria.search.toLowerCase();
                    filteredEmployees = filteredEmployees.filter(employee =>
                        employee.Name?.toLowerCase().includes(searchLower) ||
                        employee["Contact Information"]?.Email?.toLowerCase().includes(searchLower)
                    );
                }

                if (filterCriteria.skills) {
                    const skillsToMatch = filterCriteria.skills.toLowerCase().split(',').map(s => s.trim());
                    filteredEmployees = filteredEmployees.filter(employee => {
                        const employeeSkills = employee.Skills?.map(s => s.toLowerCase()) || [];

                        // Check if employee has at least one of the required skills
                        // This is the key change - we check if ANY skill matches, not ALL skills
                        return skillsToMatch.some(skill =>
                            employeeSkills.some(empSkill => empSkill.includes(skill))
                        );
                    });
                }

                if (filterCriteria.experienceLevel) {
                    filteredEmployees = filteredEmployees.filter(employee => {
                        const yearsOfExperience = employee._derived?.total_years_experience ||
                            (employee.Experience?.length || 0);

                        switch (filterCriteria.experienceLevel) {
                            case "Junior":
                                return yearsOfExperience < 2;
                            case "Mid-level":
                                return yearsOfExperience >= 2 && yearsOfExperience < 5;
                            case "Senior":
                                return yearsOfExperience >= 5 && yearsOfExperience < 8;
                            case "Lead":
                                return yearsOfExperience >= 8;
                            default:
                                return true;
                        }
                    });
                }
            }

            return {
                success: true,
                data: filteredEmployees,
                total: filteredEmployees.length
            };
        } catch (error) {
            console.error('Error filtering employees:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to filter employees',
                data: []
            };
        }
    },

    /**
     * Match employees to project criteria and generate specialized KPIs
     * @param {Object} matchData - The matching criteria and KPI data
     * @returns {Promise<Object>} - The API response
     */
    matchEmployeesWithKPIs: async (matchData) => {
        try {
            const response = await api.post('/employees/match-with-kpis', matchData);
            return response.data;
        } catch (error) {
            console.error('Error matching employees with KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to match employees',
                matched_employees: []
            };
        }
    },

    /**
     * Analyze role alignment for an employee
     * @param {string} employeeId - The ID of the employee
     * @param {Object} roleData - The role criteria and project context
     * @returns {Promise<Object>} - The API response
     */
    analyzeRoleAlignment: async (employeeId, roleData) => {
        try {
            const response = await api.post(`/employees/${employeeId}/role-alignment`, roleData);
            return response.data;
        } catch (error) {
            console.error('Error analyzing role alignment:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to analyze role alignment'
            };
        }
    },

    /**
     * Match employees with team context
     * @param {Object} matchData - The matching criteria including existing team
     * @returns {Promise<Object>} - The API response
     */
    matchWithTeamContext: async (data) => {
        try {
            const response = await api.post('/employees/match-with-team-context', data);
            return response.data;
        } catch (error) {
            console.error('Error matching with team context:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to match with team context',
                matched_employees: []
            };
        }
    }
};