import { api } from './api';

// Project service for handling project-related API calls
export const projectService = {
    /**
     * Create a new project
     * @param {Object} projectData - The project data
     * @returns {Promise<Object>} - The API response
     */
    createProject: async (projectData) => {
        try {
            const response = await api.post('/projects', projectData);
            return response.data;
        } catch (error) {
            console.error('Error creating project:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to create project'
            };
        }
    },

    /**
     * Get all projects
     * @returns {Promise<Object>} - The API response
     */
    getAllProjects: async () => {
        try {
            const response = await api.get('/projects');
            return response.data;
        } catch (error) {
            console.error('Error getting projects:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get projects',
                data: []
            };
        }
    },

    /**
     * Get a specific project by ID
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    getProject: async (projectId) => {
        try {
            const response = await api.get(`/projects/${projectId}`);
            return response.data;
        } catch (error) {
            console.error('Error getting project:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get project'
            };
        }
    },

    /**
     * Update a project
     * @param {string} projectId - The ID of the project
     * @param {Object} projectData - The updated project data
     * @returns {Promise<Object>} - The API response
     */
    updateProject: async (projectId, projectData) => {
        try {
            const response = await api.put(`/projects/${projectId}`, projectData);
            return response.data;
        } catch (error) {
            console.error('Error updating project:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to update project'
            };
        }
    },

    /**
     * Delete a project
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    deleteProject: async (projectId) => {
        try {
            const response = await api.delete(`/projects/${projectId}`);
            return response.data;
        } catch (error) {
            console.error('Error deleting project:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to delete project'
            };
        }
    },

    /**
     * Get a project's team composition
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    getProjectTeam: async (projectId) => {
        try {
            const response = await api.get(`/projects/${projectId}/team`);
            return response.data;
        } catch (error) {
            console.error('Error getting project team:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get project team'
            };
        }
    },

    /**
     * Match employees to a project
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    matchEmployeesToProject: async (projectId) => {
        try {
            const response = await api.post(`/projects/${projectId}/match-employees`);
            return response.data;
        } catch (error) {
            console.error('Error matching employees to project:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to match employees to project'
            };
        }
    },

    /**
 * Add an employee to a specific team role
 * @param {string} projectId - The ID of the project
 * @param {string} employeeId - The ID of the employee
 * @param {string} roleId - The ID of the role
 * @param {string} roleName - The name of the role
 * @returns {Promise<Object>} - The API response
 */
    addEmployeeToRole: async (projectId, employeeId, roleId, roleName) => {
        try {
            // Validate inputs before making the API call
            if (!projectId || !employeeId || !roleId) {
                console.error("Missing required parameters for addEmployeeToRole:", {
                    projectId, employeeId, roleId, roleName
                });
                return {
                    success: false,
                    message: "Missing required data for employee assignment"
                };
            }

            // Add debug logging
            console.log("Making API call to add employee to role:", {
                projectId, employeeId, roleId, roleName: roleName || "Unknown Role"
            });

            const response = await api.post(`/projects/${projectId}/team/add-employee`, {
                employeeId,
                roleId,
                roleName: roleName || "Unknown Role"
            });

            console.log("API response:", response.data);
            return response.data;
        } catch (error) {
            console.error('Error adding employee to role:', error);
            // Provide more detailed error information
            const errorMessage = error.response?.data?.message || 'Failed to add employee to role';
            console.error('Error details:', errorMessage);

            return {
                success: false,
                message: errorMessage
            };
        }
    },

    /**
     * Optimize team composition for a project
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    optimizeTeam: async (projectId) => {
        try {
            const response = await api.post(`/projects/${projectId}/optimize-team`);
            return response.data;
        } catch (error) {
            console.error('Error optimizing team:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to optimize team'
            };
        }
    }
};