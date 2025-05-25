// frontend/src/services/kpiService.js

import { api } from './api';

// KPI service for handling KPI-related API calls
export const kpiService = {
    /**
     * Generate KPIs based on project details
     * @param {Object} projectDetails - The project details
     * @returns {Promise<Object>} - The API response
     */
    generateKPIs: async (projectDetails) => {
        try {
            const response = await api.post('/kpi/generate', projectDetails);
            return response.data;
        } catch (error) {
            console.error('Error generating KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to generate KPIs'
            };
        }
    },

    /**
     * Create KPIs for a specific project
     * @param {string} projectId - The ID of the project
     * @param {Object} kpiData - The KPI data to save
     * @returns {Promise<Object>} - The API response
     */
    createProjectKPIs: async (projectId, kpiData) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/kpis`, kpiData);
            return response.data;
        } catch (error) {
            console.error('Error creating project KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to create project KPIs'
            };
        }
    },

    /**
     * Get KPIs for a specific project
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    getProjectKPIs: async (projectId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/kpis`);
            return response.data;
        } catch (error) {
            console.error('Error getting project KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get project KPIs'
            };
        }
    },

    /**
     * Get a specific chart for a project
     * @param {string} projectId - The ID of the project
     * @param {string} chartType - The type of chart (gantt, burndown, etc.)
     * @returns {Promise<Object>} - The API response
     */
    getProjectChart: async (projectId, chartType) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/charts/${chartType}`);
            return response.data;
        } catch (error) {
            console.error('Error getting project chart:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get project chart'
            };
        }
    },

    /**
     * Adjust KPIs based on project progress
     * @param {string} projectId - The ID of the project
     * @param {Object} adjustmentData - The adjustment data
     * @returns {Promise<Object>} - The API response
     */
    adjustKPIs: async (projectId, adjustmentData) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/kpis/adjust`, adjustmentData);
            return response.data;
        } catch (error) {
            console.error('Error adjusting KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to adjust KPIs'
            };
        }
    },

    /**
     * Adjust KPIs based on project changes
     * @param {string} projectId - The ID of the project
     * @param {Object} projectChanges - The project changes
     * @returns {Promise<Object>} - The API response
     */
    adjustKPIsForChanges: async (projectId, projectChanges) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/kpis/adjust-for-changes`, {
                updated_project: projectChanges
            });
            return response.data;
        } catch (error) {
            console.error('Error adjusting KPIs for changes:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to adjust KPIs for changes'
            };
        }
    },

    /**
     * Export project KPI report
     * @param {string} projectId - The ID of the project
     * @param {string} format - The export format (pdf, excel)
     * @returns {Promise<Object>} - The API response
     */
    exportKPIReport: async (projectId, format = 'pdf') => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/export?format=${format}`, {
                responseType: 'blob'
            });

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `project_kpi_report.${format}`);
            document.body.appendChild(link);
            link.click();

            return { success: true };
        } catch (error) {
            console.error('Error exporting KPI report:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to export KPI report'
            };
        }
    },

    /**
     * Get KPI metrics history for trend analysis
     * @param {string} projectId - The ID of the project
     * @param {string} metric - Specific metric to get history for
     * @returns {Promise<Object>} - The API response
     */
    getKPIHistory: async (projectId, metric = null) => {
        try {
            let url = `/kpi/projects/${projectId}/history`;
            if (metric) {
                url += `?metric=${metric}`;
            }

            const response = await api.get(url);
            return response.data;
        } catch (error) {
            console.error('Error getting KPI history:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get KPI history'
            };
        }
    },

    /**
     * Get KPI progress data by sprint
     * @param {string} projectId - The ID of the project
     * @param {number} sprintNumber - The sprint number
     * @returns {Promise<Object>} - The API response
     */
    getKPIProgressBySprint: async (projectId, sprintNumber) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/progress/${sprintNumber}`);
            return response.data;
        } catch (error) {
            console.error('Error getting KPI progress:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get KPI progress data',
                data: {}
            };
        }
    },

    /**
     * Generate KPI recommendations based on current project status
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    generateKPIRecommendations: async (projectId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/recommendations`);
            return response.data;
        } catch (error) {
            console.error('Error generating KPI recommendations:', error);
            // Check if it's a 404 error (endpoint doesn't exist)
            if (error.response && error.response.status === 404) {
                return {
                    success: true,
                    message: 'KPI recommendations feature not available',
                    recommendations: []
                };
            }
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to generate recommendations',
                recommendations: []
            };
        }
    },

    /**
     * Recalibrate KPIs mid-project
     * @param {string} projectId - The ID of the project
     * @param {Object} recalibrationData - The data for recalibration
     * @returns {Promise<Object>} - The API response
     */
    recalibrateKPIs: async (projectId, recalibrationData) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/recalibrate`, recalibrationData);
            return response.data;
        } catch (error) {
            console.error('Error recalibrating KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to recalibrate KPIs'
            };
        }
    },

    /**
     * Update individual KPI progress for an employee on a project
     * @param {string} projectId - The ID of the project
     * @param {string} employeeId - The ID of the employee
     * @param {Object} progressData - The progress data
     * @returns {Promise<Object>} - The API response
     */
    updateIndividualKPIProgress: async (projectId, employeeId, progressData) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/employees/${employeeId}/progress`, progressData);
            return response.data;
        } catch (error) {
            console.error('Error updating individual KPI progress:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to update KPI progress'
            };
        }
    },
    
    /**
     * Generate team-based KPIs
     * @param {string} projectId - The ID of the project
     * @param {Object} data - Additional data for team-based generation
     * @returns {Promise<Object>} - The API response
     */
    generateTeamBasedKPIs: async (projectId, data = {}) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/kpis/generate-team-based`, data);
            return response.data;
        } catch (error) {
            console.error('Error generating team-based KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to generate team-based KPIs'
            };
        }
    },

    /**
     * Get individual KPIs for a specific team member
     * @param {string} projectId - The ID of the project
     * @param {string} employeeId - The ID of the employee
     * @returns {Promise<Object>} - The API response
     */
    getIndividualKPIs: async (projectId, employeeId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/employees/${employeeId}/individual-kpis`);
            return response.data;
        } catch (error) {
            console.error('Error getting individual KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get individual KPIs'
            };
        }
    },

    /**
     * Predict project success
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    predictProjectSuccess: async (projectId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/kpis/predict-success`);
            return response.data;
        } catch (error) {
            console.error('Error predicting project success:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to predict project success'
            };
        }
    },

    /**
     * Get team-level KPIs for the entire team
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    getTeamLevelKPIs: async (projectId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/kpis/team-level`);
            return response.data;
        } catch (error) {
            console.error('Error getting team-level KPIs:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get team-level KPIs'
            };
        }
    },

    /**
     * Apply learning from completed projects to improve KPI accuracy
     * @param {string} projectId - The ID of the project to apply learning to
     * @param {string} referenceProjectId - The ID of the completed project to learn from
     * @returns {Promise<Object>} - The API response
     */
    applyHistoricalLearning: async (projectId, referenceProjectId = null) => {
        try {
            const payload = referenceProjectId ? { reference_project_id: referenceProjectId } : {};
            const response = await api.post(`/kpi/projects/${projectId}/kpis/apply-learning`, payload);
            return response.data;
        } catch (error) {
            console.error('Error applying historical learning:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to apply historical learning'
            };
        }
    },

    /**
     * Get KPI variance analysis comparing actual vs predicted
     * @param {string} projectId - The ID of the project
     * @returns {Promise<Object>} - The API response
     */
    getKPIVarianceAnalysis: async (projectId) => {
        try {
            const response = await api.get(`/kpi/projects/${projectId}/kpis/variance-analysis`);
            return response.data;
        } catch (error) {
            console.error('Error getting KPI variance analysis:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get variance analysis'
            };
        }
    },

    /**
     * Generate what-if scenarios for KPIs based on team changes
     * @param {string} projectId - The ID of the project
     * @param {Object} scenarioData - The scenario data (e.g., proposed team changes)
     * @returns {Promise<Object>} - The API response
     */
    generateWhatIfScenario: async (projectId, scenarioData) => {
        try {
            const response = await api.post(`/kpi/projects/${projectId}/kpis/what-if`, scenarioData);
            return response.data;
        } catch (error) {
            console.error('Error generating what-if scenario:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to generate what-if scenario'
            };
        }
    },

    /**
     * Get aggregated KPI insights across multiple projects
     * @param {Array} projectIds - Array of project IDs to analyze
     * @returns {Promise<Object>} - The API response
     */
    getAggregatedInsights: async (projectIds) => {
        try {
            const response = await api.post('/kpi/insights/aggregate', { project_ids: projectIds });
            return response.data;
        } catch (error) {
            console.error('Error getting aggregated insights:', error);
            return {
                success: false,
                message: error.response?.data?.message || 'Failed to get aggregated insights'
            };
        }
    },
};