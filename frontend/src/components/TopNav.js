import React from 'react';
import { Navbar, Nav, Container, NavDropdown, Button } from 'react-bootstrap';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { FaShieldAlt, FaUserTie, FaLandmark, FaHome, FaInfoCircle, FaPhoneAlt, FaQuestionCircle } from 'react-icons/fa';

const TopNav = () => {
    const location = useLocation();

    return (
        <Navbar bg="white" expand="lg" sticky="top" className="shadow-sm py-3 px-4 glass-card border-0 mb-0 rounded-0">
            <Container fluid>
                <Navbar.Brand as={Link} to="/" className="fw-bold text-primary fs-4 d-flex align-items-center">
                    <span className="text-gradient me-2">AI Policy Simulator</span>
                </Navbar.Brand>
                <Navbar.Toggle aria-controls="navbar-nav" />
                <Navbar.Collapse id="navbar-nav">
                    <Nav className="ms-auto align-items-center">
                        <Nav.Link as={NavLink} to="/" exact="true" className="mx-2 d-flex align-items-center fw-medium">
                            <FaHome className="me-1" /> Home
                        </Nav.Link>
                        
                        <NavDropdown title="Simulators" id="simulators-dropdown" className="mx-2 fw-medium">
                            <NavDropdown.Item as={NavLink} to="/insurance">
                                <FaShieldAlt className="me-2 text-success" /> Insurance Domain
                            </NavDropdown.Item>
                            <NavDropdown.Item as={NavLink} to="/hr">
                                <FaUserTie className="me-2 text-warning" /> HR Operations
                            </NavDropdown.Item>
                            <NavDropdown.Item as={NavLink} to="/government">
                                <FaLandmark className="me-2 text-info" /> Government Policy
                            </NavDropdown.Item>
                        </NavDropdown>

                        <Nav.Link as="a" href="/#about" className="mx-2 d-flex align-items-center fw-medium text-dark">
                            <FaInfoCircle className="me-1" /> About
                        </Nav.Link>
                        
                        <Button as="a" href="/#domains" className="btn-premium ms-lg-3 rounded-pill btn-sm py-2 px-4 shadow-sm border-0 text-white">
                            Launch App
                        </Button>
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
};

export default TopNav;
