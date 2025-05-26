import React, { useState, useEffect, useMemo } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";

const TrainingResourceList = ({
  employeeId,
  recommendations,
  onStartTraining,
}) => {
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [selectedResources, setSelectedResources] = useState({});
  const [expandedSkills, setExpandedSkills] = useState({});
  const [filterType, setFilterType] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Extract all available resources from recommendations
  const allResources = useMemo(() => {
    if (!recommendations) return {};

    const resources = {};

    // Extract from different recommendation formats
    if (recommendations.courses) {
      // New format with courses object
      Object.entries(recommendations.courses.technical || {}).forEach(([skill, courseList]) => {
        resources[skill] = { type: 'technical', resources: courseList };
      });
      Object.entries(recommendations.courses.soft || {}).forEach(([skill, courseList]) => {
        resources[skill] = { type: 'soft', resources: courseList };
      });
    } else {
      // Handle other formats
      ['technical', 'soft', 'high_priority', 'medium_priority', 'low_priority'].forEach(category => {
        if (recommendations[category] && typeof recommendations[category] === 'object') {
          Object.entries(recommendations[category]).forEach(([skill, courseList]) => {
            if (Array.isArray(courseList)) {
              resources[skill] = { type: category, resources: courseList };
            }
          });
        }
      });

      // Direct skill mapping
      Object.entries(recommendations).forEach(([key, value]) => {
        if (Array.isArray(value) && !['priority_skills', 'alternative_paths'].includes(key)) {
          resources[key] = { type: 'general', resources: value };
        }
      });
    }

    return resources;
  }, [recommendations]);

  // Filter resources based on search and type
  const filteredResources = useMemo(() => {
    let filtered = { ...allResources };

    // Apply type filter
    if (filterType !== 'all') {
      filtered = Object.fromEntries(
        Object.entries(filtered).filter(([_, data]) => data.type === filterType)
      );
    }

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = Object.fromEntries(
        Object.entries(filtered).filter(([skill, data]) => 
          skill.toLowerCase().includes(searchLower) ||
          data.resources.some(r => 
            r.name?.toLowerCase().includes(searchLower) ||
            r.provider?.toLowerCase().includes(searchLower)
          )
        )
      );
    }

    return filtered;
  }, [allResources, filterType, searchTerm]);

  const handleSkillToggle = (skill) => {
    setSelectedSkills(prev => {
      if (prev.includes(skill)) {
        // Remove skill and its resources
        const newSelected = prev.filter(s => s !== skill);
        setSelectedResources(current => {
          const updated = { ...current };
          delete updated[skill];
          return updated;
        });
        return newSelected;
      } else {
        // Add skill
        return [...prev, skill];
      }
    });

    // Toggle expansion
    setExpandedSkills(prev => ({
      ...prev,
      [skill]: !prev[skill]
    }));
  };

  const handleResourceToggle = (skill, resourceIndex) => {
    if (!selectedSkills.includes(skill)) {
      setSelectedSkills(prev => [...prev, skill]);
    }

    setSelectedResources(prev => {
      const updated = { ...prev };
      
      if (!updated[skill]) {
        updated[skill] = [];
      }

      const resources = [...updated[skill]];
      const idx = resources.indexOf(resourceIndex);
      
      if (idx > -1) {
        resources.splice(idx, 1);
      } else {
        resources.push(resourceIndex);
      }

      if (resources.length === 0) {
        delete updated[skill];
      } else {
        updated[skill] = resources;
      }

      return updated;
    });
  };

  const handleSelectAll = (skill) => {
    const skillData = filteredResources[skill];
    if (!skillData) return;

    const allIndices = skillData.resources.map((_, idx) => idx);
    
    setSelectedResources(prev => ({
      ...prev,
      [skill]: allIndices
    }));

    if (!selectedSkills.includes(skill)) {
      setSelectedSkills(prev => [...prev, skill]);
    }
  };

  const handleCreateDevelopmentPlan = () => {
    if (!employeeId || Object.keys(selectedResources).length === 0) return;

    // Prepare data for development plan
    const skillGaps = [];
    const resourcesBySkill = {};

    Object.entries(selectedResources).forEach(([skill, indices]) => {
      const skillData = allResources[skill];
      if (!skillData) return;

      skillGaps.push({ name: skill, type: skillData.type });
      resourcesBySkill[skill] = indices.map(idx => skillData.resources[idx]);
    });

    if (onStartTraining) {
      onStartTraining(skillGaps, resourcesBySkill);
    }
  };

  const getSelectedCount = () => {
    return Object.values(selectedResources).reduce((sum, indices) => sum + indices.length, 0);
  };

  const renderResource = (resource, skill, index) => {
    const isSelected = selectedResources[skill]?.includes(index) || false;

    return (
      <div
        key={`${skill}-${index}`}
        className={`border rounded-lg p-4 cursor-pointer transition-all ${
          isSelected 
            ? "border-blue-500 bg-blue-50 shadow-md" 
            : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
        }`}
        onClick={() => handleResourceToggle(skill, index)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-grow pr-2">
            <h5 className="text-sm font-medium text-gray-800 mb-1">
              {resource.name}
            </h5>
            <p className="text-xs text-gray-600">
              by {resource.provider}
            </p>
          </div>
          <div className="flex items-center space-x-2">
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
            <div
              className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-all ${
                isSelected
                  ? "bg-blue-500 border-blue-500"
                  : "bg-white border-gray-300"
              }`}
            >
              {isSelected && (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </div>
        </div>

        {resource.description && (
          <p className="mt-2 text-xs text-gray-600 line-clamp-2">
            {resource.description}
          </p>
        )}

        <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-3">
            {resource.duration && (
              <span className="flex items-center">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {resource.duration}
              </span>
            )}
            {resource.cost && (
              <span className="flex items-center">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {resource.cost}
              </span>
            )}
          </div>
          {resource.level && (
            <span className="text-xs font-medium text-gray-600">
              Level: {resource.level}
            </span>
          )}
        </div>
      </div>
    );
  };

  if (!recommendations || Object.keys(allResources).length === 0) {
    return (
      <Card title="Training Resources Library">
        <div className="py-12 text-center">
          <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <p className="text-gray-500 mb-4">No training resources available.</p>
          <p className="text-sm text-gray-400">Complete skill gap analysis to see personalized recommendations.</p>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      title="Training Resources Library"
      subtitle="Browse and select training resources to create your personalized development plan"
    >
      <div className="space-y-6">
        {/* Filters and Search */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Resources
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by skill or resource name..."
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Type
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="technical">Technical Skills</option>
                <option value="soft">Soft Skills</option>
                <option value="high_priority">High Priority</option>
                <option value="medium_priority">Medium Priority</option>
                <option value="low_priority">Low Priority</option>
              </select>
            </div>
          </div>

          {/* Selection Summary */}
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {Object.keys(filteredResources).length} skills available
            </p>
            {getSelectedCount() > 0 && (
              <p className="text-sm font-medium text-blue-600">
                {getSelectedCount()} resources selected
              </p>
            )}
          </div>
        </div>

        {/* Resources by Skill */}
        <div className="space-y-6">
          {Object.entries(filteredResources).map(([skill, skillData]) => {
            const isExpanded = expandedSkills[skill] || selectedSkills.includes(skill);
            const selectedCount = selectedResources[skill]?.length || 0;

            return (
              <div key={skill} className="border border-gray-200 rounded-lg overflow-hidden">
                <div
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedSkills.includes(skill) ? 'bg-blue-50' : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => handleSkillToggle(skill)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`h-6 w-6 rounded border-2 flex items-center justify-center transition-all ${
                          selectedSkills.includes(skill)
                            ? "bg-blue-500 border-blue-500"
                            : "bg-white border-gray-300"
                        }`}
                      >
                        {selectedSkills.includes(skill) && (
                          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <h3 className="font-medium text-gray-800">{skill}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        skillData.type === 'technical' ? 'bg-blue-100 text-blue-800' :
                        skillData.type === 'soft' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {skillData.type}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      {selectedCount > 0 && (
                        <span className="text-sm text-blue-600 font-medium">
                          {selectedCount}/{skillData.resources.length} selected
                        </span>
                      )}
                      <span className="text-sm text-gray-500">
                        {skillData.resources.length} resources
                      </span>
                      <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${
                          isExpanded ? 'transform rotate-180' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <div className="p-4 bg-white border-t border-gray-200">
                    <div className="flex justify-between items-center mb-3">
                      <p className="text-sm text-gray-600">
                        Select resources to include in your development plan
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectAll(skill);
                        }}
                      >
                        Select All
                      </Button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {skillData.resources.map((resource, idx) => 
                        renderResource(resource, skill, idx)
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Action Bar */}
        {getSelectedCount() > 0 && (
          <div className="sticky bottom-0 bg-white border-t border-gray-200 -mx-6 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {selectedSkills.length} skills selected
                </p>
                <p className="text-xs text-gray-600">
                  {getSelectedCount()} total resources
                </p>
              </div>
              <Button
                variant="primary"
                onClick={handleCreateDevelopmentPlan}
                icon={
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                }
              >
                Create Development Plan
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default TrainingResourceList;