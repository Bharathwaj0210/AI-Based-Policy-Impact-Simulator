import React, { useState } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaShieldAlt, FaDownload, FaChartLine } from 'react-icons/fa';
import { generatePolicyReport } from '../utils/reportGenerator';
import { downloadCSV } from '../utils/csvHelper';

const Insurance = () => {
    const [file, setFile] = useState(null);
    const [insuranceType, setInsuranceType] = useState('Health Insurance');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [shapData, setShapData] = useState([]);
    const [geminiData, setGeminiData] = useState(null);
    const [recommendations, setRecommendations] = useState([]);

    // Filters state
    const [filters, setFilters] = useState({});

    const handleUpload = async (e) => {
        if (e) e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('insurance', file, { insurance_type: insuranceType });
            setData(res.data);
            setMetrics(res.overall_metrics);
            setRecommendations(res.recommendations || []);
            
            // Default filters
            if (insuranceType === 'Health Insurance') {
                setFilters({ max_age: 60, max_bmi: 35.0, allow_smoker: 'Yes' });
            } else {
                setFilters({ 
                    max_vehicle_age: 15, 
                    min_experience: 2, 
                    max_customer_age: 70,
                    max_value_vehicle: 50000,
                    max_cylinder_capacity: 2500,
                    max_premium: 1000
                });
            }
        } catch (error) {
            console.error("Upload failed", error);
        }
        setLoading(false);
    };

    const handleFilterChange = (feature, value) => {
        setFilters(prev => ({ ...prev, [feature]: feature === 'allow_smoker' ? value : parseFloat(value) }));
    };

    const applyFilters = async () => {
        setLoading(true);
        try {
            const res = await filterDataset('insurance', data, filters, { insurance_type: insuranceType });
            const newMetrics = {
                records_evaluated: res.total_count,
                eligibility_rate: res.total_count > 0 ? res.eligible_count / res.total_count : 0,
                eligible: res.eligible_count,
                rejected: res.rejected_count
            };
            setMetrics(newMetrics);
            setRecommendations(res.recommendations || []);

            // Auto fetch SHAP & Gemini
            const [shapRes, geminiRes] = await Promise.all([
                explainModel('insurance', data, filters, { insurance_type: insuranceType }),
                getGeminiSummary('insurance', { insurance_type: insuranceType, filters, metrics: newMetrics })
            ]);
            setShapData(shapRes.shap_data);
            setGeminiData(geminiRes);
        } catch (error) {
            console.error("Simulation failed", error);
        }
        setLoading(false);
    };

    const exportData = (eligible) => {
        let filtered;
        if (insuranceType === 'Health Insurance') {
            filtered = data.filter(row => {
                const passAge = (parseFloat(row.age) || 0) <= (filters.max_age || 100);
                const passBMI = (parseFloat(row.bmi) || 0) <= (filters.max_bmi || 100);
                const passSmoker = filters.allow_smoker === 'Yes' || (row.smoker || '').toString().toLowerCase() === 'no';
                const isMatch = passAge && passBMI && passSmoker;
                return eligible ? isMatch : !isMatch;
            });
        } else {
            filtered = data.filter(row => {
                const passVehAge = (parseFloat(row.vehicle_age) || 0) <= (filters.max_vehicle_age || 100);
                const passExp = (parseFloat(row.driving_experience) || 0) >= (filters.min_experience || 0);
                const passCustAge = (parseFloat(row.customer_age) || 0) <= (filters.max_customer_age || 100);
                const passValue = (parseFloat(row.value_vehicle) || 0) <= (filters.max_value_vehicle || 1000000);
                const passCyl = (parseFloat(row.cylinder_capacity) || 0) <= (filters.max_cylinder_capacity || 10000);
                const passPrem = (parseFloat(row.premium) || 0) <= (filters.max_premium || 100000);
                
                const isMatch = passVehAge && passExp && passCustAge && passValue && passCyl && passPrem;
                return eligible ? isMatch : !isMatch;
            });
        }
        
        const filename = `${insuranceType.replace(' ', '_')}_${eligible ? 'Eligible' : 'Ineligible'}_List.csv`;
        downloadCSV(filtered, filename);
    };


    return (
        <div className="insurance-container fade-in">
            {/* Domain Hero */}
            <div className="domain-hero">
                <img src="/assets/insurance.png" alt="Insurance Domain" className="domain-hero-img" />
                <div className="domain-hero-content">
                    <h2 className="fw-bold text-primary mb-1">Insurance Policy Simulator</h2>
                    <p className="text-muted mb-0">Strategic threshold optimization for {insuranceType.toLowerCase()}.</p>
                </div>
            </div>

            <Row>
                {/* Left Sidebar: Filters */}
                <Col lg={4} className="mb-4">
                    <div className="filter-panel">
                        {/* Domain Switcher */}
                        <Card className="simulator-card shadow-sm border-0 mb-4 bg-light">
                            <Card.Body className="p-3">
                                <Form.Group>
                                    <Form.Label className="small fw-bold text-muted mb-2">Simulation Mode</Form.Label>
                                    <Form.Select 
                                        size="sm" 
                                        value={insuranceType} 
                                        onChange={(e) => {
                                            setInsuranceType(e.target.value);
                                            setData([]); // Reset on mode change
                                            setMetrics(null);
                                        }}
                                        className="rounded-pill border-0 shadow-sm"
                                    >
                                        <option value="Health Insurance">🏥 Health Insurance</option>
                                        <option value="Vehicle Insurance">🚗 Vehicle Insurance</option>
                                    </Form.Select>
                                </Form.Group>
                            </Card.Body>
                        </Card>

                        {/* File Upload Card */}
                        {!data.length && (
                            <Card className="simulator-card shadow-sm border-0 mb-4">
                                <Card.Body className="p-4 text-center">
                                    <FaUpload size={40} className="text-primary opacity-25 mb-3" />
                                    <h6 className="fw-bold">Step 1: Load Dataset</h6>
                                    <p className="small text-muted mb-3">Please upload your insurance master file to begin impact analysis.</p>
                                    
                                    <div className="bg-light p-3 rounded-4 mb-4 text-start border border-primary border-opacity-10">
                                        <p className="small fw-bold text-primary mb-2">Required CSV Columns:</p>
                                        <code className="x-small d-block text-muted" style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                                            {insuranceType === 'Health Insurance' 
                                                ? 'age, sex, bmi, children, smoker, region'
                                                : 'vehicle_age, vehicle_type, engine_capacity, fuel_type, vehicle_value, owner_age, owner_gender, driving_experience_years, accident_history, annual_mileage, claim_frequency, no_claim_bonus, policy_type, urban_vs_rural'
                                            }
                                        </code>
                                    </div>

                                    <Form.Group className="mb-3">
                                        <Form.Control type="file" onChange={(e) => setFile(e.target.files[0])} size="sm" className="rounded-pill" />
                                    </Form.Group>
                                    <Button onClick={handleUpload} disabled={!file || loading} className="btn-premium w-100 rounded-pill">
                                        {loading ? <Spinner size="sm" /> : 'Start Simulation'}
                                    </Button>
                                </Card.Body>
                            </Card>
                        )}

                        {data.length > 0 && (
                            <Card className="simulator-card shadow-sm border-0 mb-4">
                                <Card.Header className="bg-white border-bottom-0 pt-4 px-4">
                                    <h5 className="mb-0 small fw-bold text-uppercase tracking-wider text-primary">
                                        <FaFilter className="me-2" /> Policy Thresholds
                                    </h5>
                                </Card.Header>
                                <Card.Body className="px-4 pb-4">
                                    {insuranceType === 'Health Insurance' ? (
                                        <>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Applicant Age <span>{filters.max_age || 60}</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="18" max="100"
                                                    value={filters.max_age || 60} 
                                                    onChange={(e) => handleFilterChange('max_age', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max BMI Threshold <span>{filters.max_bmi || 35}</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="15" max="50" step="0.5"
                                                    value={filters.max_bmi || 35} 
                                                    onChange={(e) => handleFilterChange('max_bmi', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="small fw-bold mb-2">Allow Smoker</Form.Label>
                                                <Form.Select size="sm" className="rounded-pill border-0 shadow-sm"
                                                    value={filters.allow_smoker || 'Yes'}
                                                    onChange={(e) => handleFilterChange('allow_smoker', e.target.value)}
                                                >
                                                    <option value="Yes">Yes</option>
                                                    <option value="No">No</option>
                                                </Form.Select>
                                            </Form.Group>
                                        </>
                                    ) : (
                                        <>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Driver Age <span>{filters.max_customer_age || 70}</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="18" max="100"
                                                    value={filters.max_customer_age || 70} 
                                                    onChange={(e) => handleFilterChange('max_customer_age', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Min Driver Experience <span>{filters.min_experience || 2}y</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="0" max="50"
                                                    value={filters.min_experience || 2} 
                                                    onChange={(e) => handleFilterChange('min_experience', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Vehicle Value <span>${(filters.max_value_vehicle || 50000).toLocaleString()}</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="1000" max="100000" step="1000"
                                                    value={filters.max_value_vehicle || 50000} 
                                                    onChange={(e) => handleFilterChange('max_value_vehicle', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Cylinder Capacity <span>{filters.max_cylinder_capacity || 2500}cc</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="500" max="6000" step="100"
                                                    value={filters.max_cylinder_capacity || 2500} 
                                                    onChange={(e) => handleFilterChange('max_cylinder_capacity', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Premium Target <span>${filters.max_premium || 1000}</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="100" max="5000" step="50"
                                                    value={filters.max_premium || 1000} 
                                                    onChange={(e) => handleFilterChange('max_premium', e.target.value)} />
                                            </Form.Group>
                                            <Form.Group className="mb-4">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    Max Vehicle Age <span>{filters.max_vehicle_age || 15}y</span>
                                                </Form.Label>
                                                <input type="range" className="form-range" min="0" max="40"
                                                    value={filters.max_vehicle_age || 15} 
                                                    onChange={(e) => handleFilterChange('max_vehicle_age', e.target.value)} />
                                            </Form.Group>
                                        </>
                                    )}

                                    <Button onClick={applyFilters} className="btn-premium w-100 py-2 shadow-sm rounded-pill" disabled={loading}>
                                        {loading ? <Spinner size="sm" /> : 'Apply & Analyze'}
                                    </Button>

                                    {recommendations.length > 0 && (
                                        <div className="mt-4 p-3 bg-light rounded-4 border border-success border-dashed">
                                            <h6 className="text-success small fw-bold mb-2">⭐ ML Strategy Guide</h6>
                                            <ul className="small mb-0 ps-3">
                                                {recommendations.map((r, i) => (
                                                    <li key={i} className="mb-1 text-muted">{r}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>
                        )}
                    </div>
                </Col>

                {/* Right Content: Insights & AI */}
                <Col lg={8}>
                    {metrics ? (
                        <>
                            <Row className="g-3 mb-4">
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm">
                                        <small className="text-muted d-block mb-1">Evaluated</small>
                                        <h4 className="fw-bold mb-0">{metrics.records_evaluated}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-success border-4">
                                        <small className="text-muted d-block mb-1">Eligible</small>
                                        <h4 className="fw-bold mb-0 text-success">{metrics.eligible}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-danger border-4">
                                        <small className="text-muted d-block mb-1">Rejected</small>
                                        <h4 className="fw-bold mb-0 text-danger">{metrics.rejected}</h4>
                                    </Card>
                                </Col>
                            </Row>

                            <Card className="simulator-card border-0 mb-4 overflow-hidden shadow-sm">
                                <Card.Header className="bg-white border-bottom-0 pt-4 px-4 d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0"><FaChartBar className="me-2 text-info" /> Eligibility Trends</h5>
                                    <div className="metric-badge bg-info bg-opacity-10 text-info">
                                        Success Rate: {(metrics.eligibility_rate * 100).toFixed(1)}%
                                    </div>
                                    <div className="d-flex gap-2">
                                        <Button variant="outline-success" size="sm" className="rounded-pill" onClick={() => exportData(true)}>
                                            <FaDownload className="me-1" /> Eligible CSV
                                        </Button>
                                        <Button variant="outline-danger" size="sm" className="rounded-pill" onClick={() => exportData(false)}>
                                            <FaDownload className="me-1" /> Ineligible CSV
                                        </Button>
                                    </div>
                                </Card.Header>
                                <Card.Body className="p-4">
                                    <div style={{ height: '300px', minHeight: '300px' }}>
                                        <ResponsiveContainer width="100%" height="100%" minHeight={300}>
                                            <BarChart data={[
                                                { name: 'Eligible', count: metrics.eligible, fill: '#27ae60' },
                                                { name: 'Rejected', count: metrics.rejected, fill: '#e74c3c' }
                                            ]}>
                                                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                                                <YAxis axisLine={false} tickLine={false} />
                                                <Tooltip cursor={{fill: 'rgba(0,0,0,0.02)'}} />
                                                <Bar dataKey="count" radius={[10, 10, 0, 0]} barSize={60} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </Card.Body>
                            </Card>

                            {/* Gemini AI Card */}
                            <Card className="simulator-card border-0 bg-primary text-white mb-4 shadow-lg">
                                <Card.Body className="p-4">
                                    <div className="d-flex justify-content-between align-items-center mb-4">
                                        <h5 className="mb-0 fs-5 fw-bold"><FaRobot className="me-2" /> Gemini Strategic Intelligence</h5>
                                        <Button variant="outline-light" size="sm" className="rounded-pill px-3 py-1" onClick={() => generatePolicyReport('insurance', metrics, filters, geminiData)}>
                                            <FaDownload className="me-1 small" /> Export Report
                                        </Button>
                                    </div>
                                    
                                    {geminiData && geminiData.scenarios ? (
                                        <div className="bg-white rounded-4 p-1 overflow-hidden shadow-sm mb-4">
                                            <div className="table-responsive">
                                                <Table hover className="mb-0 align-middle border-0">
                                                    <thead className="bg-light">
                                                        <tr className="border-0">
                                                            <th className="py-3 ps-4 border-0 text-dark small fw-bold">Scenario</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold">Strategy</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold">Market Reach</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold pe-4">Risk Control</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {geminiData.scenarios.map((s, idx) => (
                                                            <tr key={idx} className="border-bottom">
                                                                <td className="ps-4 py-3 fw-bold text-primary small">{s.scenario}</td>
                                                                <td className="py-3 text-muted small">{s.strategic_focus}</td>
                                                                <td className="py-3 text-muted small">{s.client_impact}</td>
                                                                <td className="py-3 text-muted small pe-4">{s.risk_control}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </Table>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-5 border border-light border-2 border-dashed rounded-4 opacity-50">
                                            <p className="mb-0 small">{loading ? 'System is analyzing your policy...' : 'Apply thresholds to generate Gemini analysis'}</p>
                                        </div>
                                    )}

                                    {geminiData && geminiData.overall_summary && (
                                        <div className="p-3 bg-white bg-opacity-10 rounded-4 border border-white border-opacity-10">
                                            <h6 className="fw-bold mb-2 small text-uppercase tracking-wider">Executive Summary:</h6>
                                            <p className="mb-0 small opacity-90" style={{ lineHeight: '1.6' }}>{geminiData.overall_summary}</p>
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>

                            {/* SHAP Insights */}
                            {shapData && shapData.length > 0 && (
                                <Card className="simulator-card border-0 mb-4 shadow-sm">
                                    <Card.Header className="bg-white border-bottom-0 pt-4 px-4">
                                        <h5 className="mb-0"><FaChartLine className="me-2 text-warning" /> Decision Factor Impact (SHAP)</h5>
                                    </Card.Header>
                                    <Card.Body className="p-4">
                                        <div style={{ height: '300px', minHeight: '300px' }}>
                                            <ResponsiveContainer width="100%" height="100%" minHeight={300}>
                                                <BarChart data={shapData} layout="vertical">
                                                    <XAxis type="number" hide />
                                                    <YAxis dataKey="feature" type="category" width={120} axisLine={false} tickLine={false} className="small" />
                                                    <Tooltip cursor={{fill: 'transparent'}} />
                                                    <Bar dataKey="importance" fill="#4361ee" radius={[0, 10, 10, 0]} barSize={20} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </Card.Body>
                                </Card>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-5 mt-5">
                            <FaShieldAlt size={80} className="text-light mb-4" />
                            <h3 className="text-muted">No Simulation Active</h3>
                            <p className="text-muted">Upload your dataset in the sidebar to begin analyzing policy impacts.</p>
                        </div>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default Insurance;
