import React, { useState, useEffect } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import Loading from "../common/Loading";
import Modal from "../common/Modal";
import { recommendationService } from "../../services/recommendationService";

const DevelopmentTracker = ({ employeeId, planId }) => {
  const [developmentPlan, setDevelopmentPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressValue, setProgressValue] = useState(0);
  const [completedResources, setCompletedResources] = useState([]);

  useEffect(() => {
    if (employeeId && planId) {
      fetchDevelopmentPlan();
    }
  }, [employeeId, planId]);

  const fetchDevelopmentPlan = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await recommendationService.getDevelopmentPlan(
        employeeId,
        planId
      );

      if (response.success) {
        setDevelopmentPlan(response.development_plan);
      } else {
        setError(response.message || "Failed to fetch development plan");
      }
    } catch (error) {
      console.error("Error fetching development plan:", error);
      setError("An error occurred while fetching the development plan");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateProgress = async () => {
    if (!selectedSkill) return;

    setIsUpdating(true);
    setUpdateSuccess(false);

    try {
      const response = await recommendationService.trackProgress(
        employeeId,
        planId,
        selectedSkill.name,
        progressValue / 100, // Convert to 0-1 range
        completedResources
      );

      if (response.success) {
        setDevelopmentPlan(response.updated_plan);
        setUpdateSuccess(true);
        setTimeout(() => {
          setShowProgressModal(false);
          setSelectedSkill(null);
          setProgressValue(0);
          setCompletedResources([]);
          setUpdateSuccess(false);
        }, 1500);
      } else {
        setError(response.message || "Failed to update progress");
      }
    } catch (error) {
      console.error("Error updating progress:", error);
      setError("An error occurred while updating progress");
    } finally {
      setIsUpdating(false);
    }
  };

  const openProgressModal = (skill) => {
    setSelectedSkill(skill);
    setProgressValue(Math.round((skill.progress || 0) * 100));
    setCompletedResources(
      skill.resources
        ?.filter(r => r.completed)
        .map(r => r.name) || []
    );
    setShowProgressModal(true);
  };

  const toggleResourceCompletion = (resourceName) => {
    setCompletedResources(prev => {
      if (prev.includes(resourceName)) {
        return prev.filter(name => name !== resourceName);
      } else {
        return [...prev, resourceName];
      }
    });
  };

  const getProgressColor = (progress) => {
    if (progress >= 0.8) return "bg-green-500";
    if (progress >= 0.4) return "bg-yellow-500";
    return "bg-blue-500";
  };

  const getStatusBadge = (progress) => {
    if (progress >= 1) return { text: "Completed", color: "bg-green-100 text-green-800" };
    if (progress >= 0.7) return { text: "Advanced", color: "bg-blue-100 text-blue-800" };
    if (progress >= 0.3) return { text: "In Progress", color: "bg-yellow-100 text-yellow-800" };
    if (progress > 0) return { text: "Started", color: "bg-purple-100 text-purple-800" };
    return { text: "Not Started", color: "bg-gray-100 text-gray-800" };
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getDaysRemaining = (targetDate) => {
    if (!targetDate) return null;
    const target = new Date(targetDate);
    const today = new Date();
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const closeModal = () => {
    setShowProgressModal(false);
    setSelectedSkill(null);
    setProgressValue(0);
    setCompletedResources([]);
  };

  if (isLoading) {
    return (
      <Card title="Development Plan Progress">
        <div className="py-8">
          <Loading text="Loading development plan..." />
        </div>
      </Card>
    );
  }

  if (error && !developmentPlan) {
    return (
      <Card title="Development Plan Progress">
        <div className="p-4 text-red-700 rounded-md bg-red-50">
          <p>{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={fetchDevelopmentPlan}
          >
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!developmentPlan) {
    return (
      <Card title="Development Plan Progress">
        <div className="py-8 text-center text-gray-500">
          No development plan found.
        </div>
      </Card>
    );
  }

  const overallProgress = developmentPlan.overall_progress || 0;
  const daysRemaining = getDaysRemaining(developmentPlan.end_date);

  // Modal footer content
  const modalFooter = (
    <>
      <Button
        variant="outline"
        onClick={closeModal}
        disabled={isUpdating}
      >
        Cancel
      </Button>
      <Button
        variant="primary"
        onClick={handleUpdateProgress}
        disabled={isUpdating}
        className="ml-3"
        icon={
          isUpdating ? (
            <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : null
        }
      >
        {isUpdating ? "Updating..." : "Update Progress"}
      </Button>
    </>
  );

  return (
    <>
      <Card
        title="Development Plan Progress"
        subtitle={`Track your learning journey and update progress`}
      >
        <div className="space-y-6">
          {/* Plan Overview */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-gray-600 mb-1">Started</p>
                <p className="font-medium text-gray-800">
                  {formatDate(developmentPlan.start_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Target Completion</p>
                <p className="font-medium text-gray-800">
                  {formatDate(developmentPlan.end_date)}
                </p>
                {daysRemaining !== null && (
                  <p className={`text-xs mt-1 ${
                    daysRemaining < 0 ? 'text-red-600' :
                    daysRemaining < 30 ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {daysRemaining < 0 
                      ? `${Math.abs(daysRemaining)} days overdue`
                      : `${daysRemaining} days remaining`
                    }
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Overall Progress</p>
                <div className="flex items-center">
                  <div className="flex-grow mr-3">
                    <div className="h-3 bg-gray-200 rounded-full">
                      <div
                        className={`h-full rounded-full transition-all ${getProgressColor(overallProgress)}`}
                        style={{ width: `${overallProgress * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <span className="text-lg font-bold text-gray-800">
                    {Math.round(overallProgress * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Skills Progress */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Skills Progress
            </h3>

            {developmentPlan.skills?.map((skill, index) => {
              const progress = skill.progress || 0;
              const status = getStatusBadge(progress);
              const daysUntilTarget = getDaysRemaining(skill.target_date);
              const completedResourceCount = skill.resources?.filter(r => r.completed).length || 0;
              const totalResourceCount = skill.resources?.length || 0;

              return (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-800">{skill.name}</h4>
                      <div className="flex items-center mt-1 space-x-3">
                        <span className={`text-xs px-2 py-0.5 rounded ${status.color}`}>
                          {status.text}
                        </span>
                        {daysUntilTarget !== null && (
                          <span className={`text-xs ${
                            daysUntilTarget < 0 ? 'text-red-600' :
                            daysUntilTarget < 14 ? 'text-yellow-600' :
                            'text-gray-600'
                          }`}>
                            Due in {daysUntilTarget} days
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openProgressModal(skill)}
                      icon={
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      }
                    >
                      Update
                    </Button>
                  </div>

                  <div className="mb-3">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs text-gray-600">Progress</span>
                      <span className="text-xs font-medium text-gray-800">
                        {Math.round(progress * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className={`h-full rounded-full transition-all ${getProgressColor(progress)}`}
                        style={{ width: `${progress * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {totalResourceCount > 0 && (
                    <div className="text-xs text-gray-600">
                      <span className="font-medium">{completedResourceCount}/{totalResourceCount}</span> resources completed
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Success Message */}
          {updateSuccess && (
            <div className="p-3 text-green-700 rounded-md bg-green-50 animate-fade-in">
              Progress updated successfully!
            </div>
          )}
        </div>
      </Card>

      {/* Progress Update Modal */}
      <Modal
        isOpen={showProgressModal}
        onClose={closeModal}
        title={`Update Progress: ${selectedSkill?.name}`}
        footer={modalFooter}
        size="md"
      >
        {selectedSkill && (
          <div className="space-y-6">
            {/* Progress Slider */}
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                Overall Progress
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={progressValue}
                  onChange={(e) => setProgressValue(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${progressValue}%, #E5E7EB ${progressValue}%, #E5E7EB 100%)`
                  }}
                />
                <div className="flex justify-between text-xs text-gray-600">
                  <span>0%</span>
                  <span className="font-medium text-lg text-gray-800">{progressValue}%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>

            {/* Resources Checklist */}
            {selectedSkill.resources && selectedSkill.resources.length > 0 && (
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  Completed Resources
                </label>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedSkill.resources.map((resource, idx) => (
                    <label
                      key={idx}
                      className="flex items-start p-3 bg-gray-50 rounded-md cursor-pointer hover:bg-gray-100"
                    >
                      <input
                        type="checkbox"
                        checked={completedResources.includes(resource.name)}
                        onChange={() => toggleResourceCompletion(resource.name)}
                        className="mt-0.5 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-800">
                          {resource.name}
                        </p>
                        <p className="text-xs text-gray-600">
                          {resource.provider} • {resource.type}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Progress Tips */}
            <div className="bg-blue-50 rounded-md p-3">
              <p className="text-xs text-blue-800">
                <strong>Tip:</strong> Update your progress regularly to stay motivated and track your learning journey effectively.
              </p>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default DevelopmentTracker;