// src/components/Navbar.tsx
import { Link, useNavigate } from "react-router-dom";

interface NavbarProps {
  token: string | null;
  onLogout: () => void;
}

export default function Navbar({ token, onLogout }: NavbarProps) {
  const navigate = useNavigate();

  const handleLogoutClick = () => {
    onLogout();
    navigate("/login");
  };

  return (
    <nav style={{ padding: "10px", backgroundColor: "#f0f0f0" }}>
      {token ? (
        <>
          <Link to="/dashboard" style={{ marginRight: "10px" }}>
            Dashboard
          </Link>
          <button onClick={handleLogoutClick}>Logout</button>
        </>
      ) : (
        <>
          <Link to="/login" style={{ marginRight: "10px" }}>
            Login
          </Link>
          <Link to="/register">Register</Link>
        </>
      )}
    </nav>
  );
}
