import React from 'react';
import { Row, Col, Card, Button, Container } from 'react-bootstrap';
import { FaShieldAlt, FaUserTie, FaLandmark, FaRobot, FaChartLine, FaCheckCircle } from 'react-icons/fa';

const Home = () => {
    return (
        <div className="home-container fade-in">
            {/* Hero Section */}
            <section className="hero-section text-center">
                <Container>
                    <Row className="justify-content-center align-items-center">
                        <Col lg={7}>
                            <h1 className="display-3 fw-bold mb-4">
                                <span className="text-gradient">AI Policy Impact</span> <br />
                                Simulator
                            </h1>
                            <p className="lead text-muted mb-5 px-lg-5">
                                Leverage state-of-the-art Generative AI and Explainable ML to simulate, 
                                analyze, and optimize strategic policy decisions across Insurance, HR, and Governance.
                            </p>
                            <div className="d-flex justify-content-center gap-3">
                                <Button href="#domains" className="btn-premium px-5 py-3 shadow-lg">
                                    Launch Simulator
                                </Button>
                                <Button href="#about" variant="outline-primary" className="rounded-pill px-5 py-3 fw-bold">
                                    Learn More
                                </Button>
                            </div>
                        </Col>
                        <Col lg={5} className="mt-5 mt-lg-0">
                            <div className="hero-image-container">
                                <img src="/assets/hero.png" alt="AI Policy Illustration" className="img-fluid" />
                                <div className="hero-image-overlay"></div>
                            </div>
                        </Col>
                    </Row>
                </Container>
            </section>

            {/* About Section */}
            <section id="about" className="py-5 bg-white border-top">
                <Container className="py-5">
                    <Row className="mb-5 text-center">
                        <Col lg={8} className="mx-auto">
                            <h2 className="fw-bold mb-3">About the Project</h2>
                            <p className="text-muted">
                                Our platform empowers decision-makers with data-driven simulations. By combining traditional workforce and demographic analysis with Google Gemini's strategic reasoning, we provide a 360° view of policy impact.
                            </p>
                        </Col>
                    </Row>
                    <Row className="g-4">
                        {[
                            { icon: <FaRobot />, title: "Gemini Strategic AI", desc: "Automated analysis of policy scenarios with detailed strategic breakdowns." },
                            { icon: <FaChartLine />, title: "Explainable ML", desc: "Understand exactly which factors drive your policy reach using SHAP values." },
                            { icon: <FaCheckCircle />, title: "Impact Auditing", desc: "Minimize bias and maximize inclusion through real-time threshold testing." }
                        ].map((item, idx) => (
                            <Col md={4} key={idx}>
                                <div className="p-4 text-center rounded-4 border-0 hover-lift h-100 bg-light">
                                    <div className="feature-icon-wrapper mx-auto mb-3 text-primary fs-3">
                                        {item.icon}
                                    </div>
                                    <h5 className="fw-bold">{item.title}</h5>
                                    <p className="small text-muted mb-0">{item.desc}</p>
                                </div>
                            </Col>
                        ))}
                    </Row>
                </Container>
            </section>

            {/* Domains Section */}
            <section id="domains" className="py-5 bg-light">
                <Container className="py-5">
                    <div className="text-center mb-5">
                        <h6 className="text-primary fw-bold text-uppercase tracking-wider mb-2">Simulation Hub</h6>
                        <h2 className="display-5 fw-bold">Select Your Domain</h2>
                        <p className="text-muted">Choose a specialized model to begin your impact analysis.</p>
                    </div>

                    <Row className="justify-content-center g-4">
                        {/* Insurance Card */}
                        <Col md={4}>
                            <Card className="feature-card h-100 shadow-hover border-0 overflow-hidden">
                                <div className="bg-primary bg-opacity-10 d-flex align-items-center justify-content-center" style={{ height: '200px' }}>
                                    <img src="/assets/insurance.png" alt="Insurance" className="img-fluid" style={{ maxHeight: '160px', width: 'auto' }} 
                                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
                                    <FaShieldAlt className="text-primary display-4" style={{ display: 'none' }} />
                                </div>
                                <Card.Body className="p-4">
                                    <div className="d-flex align-items-center mb-3">
                                        <h4 className="fw-bold mb-0">Insurance</h4>
                                    </div>
                                    <Card.Text className="text-muted small mb-4">
                                        Model Health and Vehicle policy reach. Optimize premium thresholds while managing risk exposure.
                                    </Card.Text>
                                    <Button href="/insurance" variant="primary" className="w-100 rounded-pill py-2 fw-bold">
                                        Launch Module
                                    </Button>
                                </Card.Body>
                            </Card>
                        </Col>

                        {/* HR Card */}
                        <Col md={4}>
                            <Card className="feature-card h-100 shadow-hover border-0 overflow-hidden">
                                <div className="bg-warning bg-opacity-10 d-flex align-items-center justify-content-center" style={{ height: '200px' }}>
                                    <img src="/assets/hr.png" alt="HR" className="img-fluid" style={{ maxHeight: '160px', width: 'auto' }} 
                                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
                                    <FaUserTie className="text-warning display-4" style={{ display: 'none' }} />
                                </div>
                                <Card.Body className="p-4">
                                    <div className="d-flex align-items-center mb-3">
                                        <h4 className="fw-bold mb-0">Human Resources</h4>
                                    </div>
                                    <Card.Text className="text-muted small mb-4">
                                        Simulate recruitment efficiency and attrition risk. Balance talent quality with retention targets.
                                    </Card.Text>
                                    <Button href="/hr" variant="warning" className="w-100 rounded-pill py-2 text-white fw-bold">
                                        Launch Module
                                    </Button>
                                </Card.Body>
                            </Card>
                        </Col>

                        {/* Government Card */}
                        <Col md={4}>
                            <Card className="feature-card h-100 shadow-hover border-0 overflow-hidden">
                                <div className="bg-info bg-opacity-10 d-flex align-items-center justify-content-center" style={{ height: '200px' }}>
                                    <img src="/assets/government.png" alt="Government" className="img-fluid" style={{ maxHeight: '160px', width: 'auto' }} 
                                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
                                    <FaLandmark className="text-info display-4" style={{ display: 'none' }} />
                                </div>
                                <Card.Body className="p-4">
                                    <div className="d-flex align-items-center mb-3">
                                        <h4 className="fw-bold mb-0">Government</h4>
                                    </div>
                                    <Card.Text className="text-muted small mb-4">
                                        Audit public welfare programs like scholarships and pensions. Maximize reach within budget constraints.
                                    </Card.Text>
                                    <Button href="/government" variant="info" className="w-100 rounded-pill py-2 text-white fw-bold">
                                        Launch Module
                                    </Button>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            </section>

            {/* Footer / Contact */}
            <footer className="py-5 bg-dark text-white text-center">
                <Container>
                    <h5 className="fw-bold mb-3">AI Based Policy Impact Simulator</h5>
                    <p className="small opacity-50 mb-0">© 2026 Advanced Analytics & Strategic AI. All rights reserved.</p>
                </Container>
            </footer>
        </div>
    );
};

export default Home;
