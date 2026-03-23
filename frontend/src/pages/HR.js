import React, { useState } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaUserTie, FaDownload, FaChartLine } from 'react-icons/fa';
import { generatePolicyReport } from '../utils/reportGenerator';
import { downloadCSV } from '../utils/csvHelper';

const HR = () => {
    const [file, setFile] = useState(null);
    const [hrType, setHrType] = useState('Recruitment Optimization');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [shapData, setShapData] = useState([]);
    const [geminiData, setGeminiData] = useState(null);
    const [suggestedPolicy, setSuggestedPolicy] = useState(null);

    // Filters state
    const [filters, setFilters] = useState({});

    const handleUpload = async (e) => {
        if (e) e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('hr', file, { analysis_type: hrType });
            setData(res.data);
            setMetrics(res.overall_metrics);
            setSuggestedPolicy(res.suggested_policy || res.recommendation);
            // Default filters
            setFilters({ age_min: 18, rating_min: 1, tenure_min: 0 });
        } catch (error) {
            console.error("Upload failed", error);
        }
        setLoading(false);
    };

    const handleFilterChange = (feature, value) => {
        setFilters(prev => ({ ...prev, [feature]: parseFloat(value) }));
    };

    const applyFilters = async () => {
        setLoading(true);
        try {
            const res = await filterDataset('hr', data, filters, { analysis_type: hrType });
            const newMetrics = {
                records_evaluated: res.total_count,
                eligibility_rate: res.total_count > 0 ? res.eligible_count / res.total_count : 0,
                eligible: res.eligible_count,
                rejected: res.rejected_count
            };
            setMetrics(newMetrics);
            setSuggestedPolicy(res.recommendation);

            // Auto fetch SHAP & Gemini
            const [shapRes, geminiRes] = await Promise.all([
                explainModel('hr', data, filters, { analysis_type: hrType }),
                getGeminiSummary('hr', { analysis_type: hrType, filters, metrics: newMetrics })
            ]);
            setShapData(shapRes.shap_data);
            setGeminiData(geminiRes);
        } catch (error) {
            console.error("Simulation failed", error);
        }
        setLoading(false);
    };

    const exportData = (eligible) => {
        const filtered = data.filter(row => {
            const passAge = (parseFloat(row.age) || 0) >= (filters.age_min || 18);
            const passRating = (parseFloat(row['current employee rating']) || 0) >= (filters.rating_min || 1);
            const passTenure = (parseFloat(row.tenureyears) || 0) >= (filters.tenure_min || 0);
            const isMatch = passAge && passRating && passTenure;
            return eligible ? isMatch : !isMatch;
        });

        const filename = `${hrType.replace(/\s+/g, '_')}_${eligible ? 'Eligible' : 'Ineligible'}_List.csv`;
        downloadCSV(filtered, filename);
    };


    return (
        <div className="hr-container fade-in">
            {/* Domain Hero */}
            <div className="domain-hero">
                <img src="/assets/hr.png" alt="HR Domain" className="domain-hero-img" />
                <div className="domain-hero-content">
                    <h2 className="fw-bold text-primary mb-1">HR Operations Simulator</h2>
                    <p className="text-muted mb-0">Optimize talent acquisition and employee retention with explainable AI.</p>
                </div>
            </div>

            <Row>
                {/* Left Sidebar: Filters */}
                <Col lg={4} className="mb-4">
                    <div className="filter-panel">
                        {/* Mode Switcher */}
                        <Card className="simulator-card shadow-sm border-0 mb-4 bg-light">
                            <Card.Body className="p-3">
                                <Form.Group>
                                    <Form.Label className="small fw-bold text-muted mb-2">Analysis Objective</Form.Label>
                                    <Form.Select 
                                        size="sm" 
                                        value={hrType} 
                                        onChange={(e) => {
                                            setHrType(e.target.value);
                                            setData([]);
                                            setMetrics(null);
                                        }}
                                        className="rounded-pill border-0 shadow-sm"
                                    >
                                        <option value="Recruitment Optimization">🎯 Recruitment Optimization</option>
                                        <option value="Attrition Prediction">🧠 Attrition Prediction</option>
                                    </Form.Select>
                                </Form.Group>
                            </Card.Body>
                        </Card>

                        {/* File Upload */}
                        {!data.length && (
                            <Card className="simulator-card shadow-sm border-0 mb-4">
                                <Card.Body className="p-4 text-center">
                                    <FaUpload size={40} className="text-primary opacity-25 mb-3" />
                                    <h6 className="fw-bold">Step 1: Upload Dataset</h6>
                                    <p className="small text-muted mb-3">Load your HR or candidate CSV to begin strategic modeling.</p>

                                    <div className="bg-light p-3 rounded-4 mb-4 text-start border border-primary border-opacity-10">
                                        <p className="small fw-bold text-primary mb-2">Required CSV Columns:</p>
                                        <code className="x-small d-block text-muted" style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                                            age, tenureyears, performance score, current employee rating, isactive
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
                                        <FaFilter className="me-2" /> Policy Filters
                                    </h5>
                                </Card.Header>
                                <Card.Body className="px-4 pb-4">
                                    <Form.Group className="mb-4">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            Minimum Age Threshold <span>{filters.age_min || 18}y</span>
                                        </Form.Label>
                                        <input type="range" className="form-range" min="18" max="65"
                                            value={filters.age_min || 18} 
                                            onChange={(e) => handleFilterChange('age_min', e.target.value)} />
                                    </Form.Group>
                                    <Form.Group className="mb-4">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            Minimum Rating <span>{filters.rating_min || 1}★</span>
                                        </Form.Label>
                                        <input type="range" className="form-range" min="1" max="5"
                                            value={filters.rating_min || 1} 
                                            onChange={(e) => handleFilterChange('rating_min', e.target.value)} />
                                    </Form.Group>
                                    <Form.Group className="mb-4">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            Minimum Tenure <span>{filters.tenure_min || 0}y</span>
                                        </Form.Label>
                                        <input type="range" className="form-range" min="0" max="20"
                                            value={filters.tenure_min || 0} 
                                            onChange={(e) => handleFilterChange('tenure_min', e.target.value)} />
                                    </Form.Group>

                                    <Button onClick={applyFilters} className="btn-premium w-100 py-2 shadow-sm rounded-pill" disabled={loading}>
                                        {loading ? <Spinner size="sm" /> : 'Apply & Re-audit'}
                                    </Button>

                                    {suggestedPolicy && (
                                        <div className="mt-4 p-3 bg-light rounded-4 border border-warning border-dashed">
                                            <h6 className="text-warning small fw-bold mb-2">⭐ ML Strategy Guide</h6>
                                            {Array.isArray(suggestedPolicy) ? (
                                                <ul className="small mb-0 ps-3">
                                                    {suggestedPolicy.map((item, i) => <li key={i} className="text-muted">{item}</li>)}
                                                </ul>
                                            ) : (typeof suggestedPolicy === 'object' && suggestedPolicy !== null) ? (
                                                <div className="small">
                                                    {Object.entries(suggestedPolicy).map(([k, v]) => (
                                                        <div key={k} className="mb-1">
                                                            <b className="text-capitalize">{k.replace(/_/g, ' ')}</b>: {v}
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="small mb-0 text-muted">{suggestedPolicy}</p>
                                            )}
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>
                        )}
                    </div>
                </Col>

                {/* Right Content */}
                <Col lg={8}>
                    {metrics ? (
                        <>
                            <Row className="g-3 mb-4">
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm">
                                        <small className="text-muted d-block mb-1">Evaluated</small>
                                        <h4 className="fw-bold mb-0">{metrics.records_evaluated || metrics.total_records}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-success border-4">
                                        <small className="text-muted d-block mb-1">Selected/Retained</small>
                                        <h4 className="fw-bold mb-0 text-success">{metrics.eligible || metrics.best_case}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-danger border-4">
                                        <small className="text-muted d-block mb-1">Rejected/Attrition</small>
                                        <h4 className="fw-bold mb-0 text-danger">{metrics.rejected || metrics.worst_case}</h4>
                                    </Card>
                                </Col>
                            </Row>

                            <Card className="simulator-card border-0 mb-4 overflow-hidden shadow-sm">
                                <Card.Header className="bg-white border-bottom-0 pt-4 px-4 d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0"><FaChartBar className="me-2 text-info" /> Population Impact</h5>
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
                                                { name: 'Selected', count: metrics.eligible || metrics.best_case, fill: '#27ae60' },
                                                { name: 'Excluded', count: metrics.rejected || metrics.worst_case, fill: '#e74c3c' }
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
                                        <h5 className="mb-0 fs-5 fw-bold"><FaRobot className="me-2" /> Gemini Strategic HR Insights</h5>
                                        <Button variant="outline-light" size="sm" className="rounded-pill px-3 py-1" onClick={() => generatePolicyReport('hr', metrics, filters, geminiData)}>
                                            <FaDownload className="me-1 small" /> Export Analysis
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
                                                            <th className="py-3 border-0 text-dark small fw-bold">Employee Impact</th>
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
                                            <p className="mb-0 small">{loading ? 'Synthesizing strategic insights...' : 'Apply policy to see Gemini Strategic Analysis'}</p>
                                        </div>
                                    )}

                                    {geminiData && geminiData.overall_summary && (
                                        <div className="p-3 bg-white bg-opacity-10 rounded-4 border border-white border-opacity-10">
                                            <h6 className="fw-bold mb-2 small text-uppercase tracking-wider">Executive View:</h6>
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
                            <FaUserTie size={80} className="text-light mb-4" />
                            <h3 className="text-muted">HR Simulation Inactive</h3>
                            <p className="text-muted">Load employee or candidate data to begin modeling strategic impacts.</p>
                        </div>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default HR;
