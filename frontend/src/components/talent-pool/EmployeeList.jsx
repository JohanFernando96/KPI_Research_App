import React from "react";
import { Link } from "react-router-dom";
import Card from "../common/Card";
import Button from "../common/Button";

const EmployeeList = ({
  employees,
  onSelectEmployee,
  selectionMode = false,
  selectedEmployees = [],
  onEmployeeToggle,
  isLoading,
}) => {
  // Helper function to get experience level
  const getExperienceLevel = (employee) => {
    // Use _derived data if available
    if (employee._derived?.total_years_experience !== undefined) {
      const years = employee._derived.total_years_experience;
      if (years < 2)
        return { level: "Junior", color: "bg-green-100 text-green-800" };
      if (years < 5)
        return { level: "Mid-level", color: "bg-blue-100 text-blue-800" };
      if (years < 8)
        return { level: "Senior", color: "bg-purple-100 text-purple-800" };
      return { level: "Lead", color: "bg-indigo-100 text-indigo-800" };
    }

    // Fallback to simple calculation based on number of roles
    const roles = employee.Experience?.length || 0;
    if (roles < 2)
      return { level: "Junior", color: "bg-green-100 text-green-800" };
    if (roles < 3)
      return { level: "Mid-level", color: "bg-blue-100 text-blue-800" };
    if (roles < 4)
      return { level: "Senior", color: "bg-purple-100 text-purple-800" };
    return { level: "Lead", color: "bg-indigo-100 text-indigo-800" };
  };

  if (employees.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
        No employees found. Upload CVs to add employees.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {employees.map((employee) => {
        const experienceLevel = getExperienceLevel(employee);
        const isSelected =
          selectionMode &&
          selectedEmployees.some((e) => e._id === employee._id);

        return (
          <div
            key={employee._id}
            className={`p-4 transition-colors border rounded-md cursor-pointer hover:bg-gray-50 ${
              isSelected ? "border-blue-500 bg-blue-50" : ""
            }`}
            onClick={() => {
              if (selectionMode && onEmployeeToggle) {
                onEmployeeToggle(employee);
              } else if (onSelectEmployee) {
                onSelectEmployee(employee._id);
              }
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                {selectionMode && (
                  <div
                    className={`mr-3 h-5 w-5 rounded border ${
                      isSelected
                        ? "bg-blue-500 border-blue-500"
                        : "border-gray-300"
                    } flex items-center justify-center`}
                  >
                    {isSelected && (
                      <svg
                        className="w-3 h-3 text-white"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                )}
                <div>
                  <h3 className="font-medium text-gray-800 text-md">
                    {employee.Name || "Unknown"}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {employee["Contact Information"]?.Email ||
                      "No email available"}
                  </p>
                </div>
              </div>
              <span
                className={`text-xs px-2.5 py-0.5 rounded ${experienceLevel.color}`}
              >
                {experienceLevel.level}
              </span>
            </div>

            <div className="flex flex-wrap gap-1 mt-3">
              {employee.Skills?.slice(0, 5).map((skill, idx) => (
                <span
                  key={idx}
                  className="bg-gray-100 text-gray-800 text-xs px-1.5 py-0.5 rounded"
                >
                  {skill}
                </span>
              ))}
              {employee.Skills?.length > 5 && (
                <span className="bg-gray-100 text-gray-800 text-xs px-1.5 py-0.5 rounded">
                  +{employee.Skills.length - 5} more
                </span>
              )}
            </div>

            <div className="flex justify-between mt-3 text-xs text-gray-500">
              <span>
                {employee.Experience?.[0]?.Role || "Unknown Position"}
                {employee.Experience?.[0]?.Company &&
                  ` at ${employee.Experience[0].Company}`}
              </span>
              {!selectionMode && (
                <div className="flex space-x-3">
                  <Link
                    to={`/skill-development/${employee._id}`}
                    className="text-blue-600 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Skills
                  </Link>
                  <Link
                    to={`/talent-pool/${employee._id}`}
                    className="text-blue-600 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Profile
                  </Link>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default EmployeeList;
