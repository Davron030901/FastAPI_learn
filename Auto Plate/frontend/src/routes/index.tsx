import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Register from '../components/Register';
import Login from '../components/Login';
import PlateList from '../components/PlateList';
import PlateDetail from '../components/PlateDetail';

export default function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/plates"
        element={
          isAuthenticated ? <PlateList /> : <Navigate to="/login" />
        }
      />
      <Route
        path="/plates/:id"
        element={
          isAuthenticated ? <PlateDetail /> : <Navigate to="/login" />
        }
      />
      <Route path="/" element={<Navigate to="/plates" />} />
    </Routes>
  );
}