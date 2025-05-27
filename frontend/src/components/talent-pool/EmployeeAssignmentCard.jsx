import React, { useState, useEffect } from "react";
import { employeeService } from "../../services/employeeService";
import { extractId } from "../../utils/dataHelpers";

const EmployeeAssignmentCard = ({
  employeeId,
  projectId,
  roleId,
  onRemove,
}) => {
  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmployee = async () => {
      const id = extractId(employeeId);
      
      if (!id) {
        console.error('Invalid employee ID in EmployeeAssignmentCard:', employeeId);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const response = await employeeService.getEmployee(id);
        if (response.success) {
          setEmployee(response.data);
        }
      } catch (error) {
        console.error("Error fetching employee:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployee();
  }, [employeeId]);
  
  if (loading) {
    return (
      <div className="text-sm text-gray-500">Loading employee details...</div>
    );
  }

  if (!employee) {
    return (
      <div className="text-sm text-gray-500">
        Employee information unavailable
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between">
      <div>
        <div className="font-medium text-gray-800">{employee.Name}</div>
        <div className="text-xs text-gray-500">
          {employee.Experience?.[0]?.Role || "Unknown Role"}
        </div>
      </div>
      {onRemove && (
        <button
          onClick={onRemove}
          className="text-xs text-red-600 hover:text-red-800"
        >
          Remove
        </button>
      )}
    </div>
  );
};

export default EmployeeAssignmentCard;
