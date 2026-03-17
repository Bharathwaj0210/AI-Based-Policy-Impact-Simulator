import React from 'react';
import { Nav } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';
import { FaShieldAlt, FaUserTie, FaLandmark, FaHome } from 'react-icons/fa';

const Sidebar = () => {
    return (
        <div className="sidebar bg-dark text-white d-flex flex-column p-3" style={{ width: '250px', minHeight: '100vh', transition: 'all 0.3s' }}>
            <h4 className="text-center mb-4 fw-bold text-primary">AI Policy Sim</h4>
            <Nav variant="pills" className="flex-column mb-auto">
                <Nav.Item>
                    <Nav.Link as={NavLink} to="/" exact="true" className="text-white mb-2 d-flex align-items-center">
                        <FaHome className="me-2" /> Home
                    </Nav.Link>
                </Nav.Item>
                <Nav.Item>
                    <Nav.Link as={NavLink} to="/insurance" className="text-white mb-2 d-flex align-items-center">
                        <FaShieldAlt className="me-2 text-success" /> Insurance
                    </Nav.Link>
                </Nav.Item>
                <Nav.Item>
                    <Nav.Link as={NavLink} to="/hr" className="text-white mb-2 d-flex align-items-center">
                        <FaUserTie className="me-2 text-warning" /> HR
                    </Nav.Link>
                </Nav.Item>
                <Nav.Item>
                    <Nav.Link as={NavLink} to="/government" className="text-white mb-2 d-flex align-items-center">
                        <FaLandmark className="me-2 text-info" /> Government
                    </Nav.Link>
                </Nav.Item>
            </Nav>
            <hr />
            <div className="text-center small text-muted">
                v1.0.0 &copy; 2026
            </div>
        </div>
    );
};

export default Sidebar;
