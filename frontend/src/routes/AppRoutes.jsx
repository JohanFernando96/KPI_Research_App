import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";

// Layout components
import MainLayout from "../layouts/MainLayout";

// Page components
import Dashboard from "../pages/Dashboard";
import ProjectsPage from "../pages/ProjectsPage";
import CVUploadPage from "../pages/CVUploadPage";
import TalentPoolPage from "../pages/TalentPoolPage";
import KPIManagementPage from "../pages/KPIManagementPage";
import SkillDevelopmentPage from "../pages/SkillDevelopmentPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";

// Auth context
import { useAuth } from "../contexts/AuthContext";

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Show loading while checking authentication status
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-b-2 border-blue-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Router>
      <Routes>
        {/* Authentication routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
          }
        />

        {/* Protected routes within MainLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route index element={<Dashboard />} />

          {/* CV Management */}
          <Route path="cv-upload" element={<CVUploadPage />} />

          {/* Talent Pool */}
          <Route path="talent-pool" element={<TalentPoolPage />} />
          <Route path="talent-pool/:employeeId" element={<TalentPoolPage />} />

          {/* Projects */}
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="projects/:projectId" element={<ProjectsPage />} />
          <Route
            path="projects/:projectId/:action"
            element={<ProjectsPage />}
          />

          {/* KPI Management */}
          <Route path="kpi-management" element={<KPIManagementPage />} />
          <Route
            path="kpi-management/:projectId"
            element={<KPIManagementPage />}
          />

          {/* Skill Development */}
          <Route path="skill-development" element={<SkillDevelopmentPage />} />
          <Route
            path="skill-development/:employeeId"
            element={<SkillDevelopmentPage />}
          />
          <Route path="/skill-development" element={<SkillDevelopmentPage />} />
          <Route path="/skill-development/:employeeId" element={<SkillDevelopmentPage />} />
        </Route>

        {/* 404 Page */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
