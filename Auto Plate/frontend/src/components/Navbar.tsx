import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { isAuthenticated, isAdmin, logout } = useAuth();

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          Auto Plate Bidding
        </Link>
        <div className="space-x-4">
          {isAuthenticated ? (
            <>
              <Link to="/plates" className="hover:text-gray-300">
                Plates
              </Link>
              {isAdmin && (
                <Link to="/plates/create" className="hover:text-gray-300">
                  Create Plate
                </Link>
              )}
              <button
                onClick={logout}
                className="hover:text-gray-300"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-gray-300">
                Login
              </Link>
              <Link to="/register" className="hover:text-gray-300">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}