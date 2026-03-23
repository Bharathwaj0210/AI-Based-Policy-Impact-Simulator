import React, { useState, useEffect } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaLandmark, FaDownload, FaChartLine } from 'react-icons/fa';
import { generatePolicyReport } from '../utils/reportGenerator';
import { downloadCSV } from '../utils/csvHelper';

const POLICY_CONDITIONS = {
    scholarship: {
        annual_income: { type: "max", label: "Max Annual Income (₹)", default: 200000, min: 10000, max: 500000, step: 5000 },
        education_level: { type: "multiselect", label: "Eligible Education Levels", options: ["UG", "PG", "Diploma", "12th", "10th", "unknown"] },
        disability_status: { type: "disability_filter", label: "Disability Status", options: ["Any", "Disabled only", "Non-disabled only"] },
        gender: { type: "multiselect_optional", label: "Gender Bias Check (optional)", options: ["Male", "Female", "Other", "unknown"] },
    },
    pension: {
        age: { type: "min", label: "Minimum Age", default: 58, min: 40, max: 85, step: 1 },
        employment_status: { type: "multiselect", label: "Eligible Employment", options: ["Employed", "Unemployed", "Self-Employed", "Retired"] },
        annual_income: { type: "max", label: "Max Annual Income (₹)", default: 150000, min: 20000, max: 500000, step: 5000 },
    },
    housing: {
        annual_income: { type: "max", label: "Max Annual Income (₹)", default: 300000, min: 50000, max: 600000, step: 10000 },
        family_size: { type: "min", label: "Min Family Size", default: 2, min: 1, max: 8, step: 1 },
        employment_status: { type: "multiselect", label: "Eligible Employment", options: ["Employed", "Unemployed", "Self-Employed", "Student"] },
        owns_house: { type: "binary", label: "Citizen Must NOT own current house", default: true },
    },
    cash_welfare: {
        annual_income: { type: "max", label: "Max Annual Income (₹)", default: 100000, min: 10000, max: 300000, step: 5000 },
        employment_status: { type: "multiselect", label: "Eligible Employment", options: ["Unemployed", "Self-Employed", "Student"] },
        disability_status: { type: "disability_filter", label: "Disability Status", options: ["Any", "Disabled only", "Non-disabled only"] },
    },
};

const Government = () => {
    const [file, setFile] = useState(null);
    const [policyType, setPolicyType] = useState('scholarship');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [shapData, setShapData] = useState([]);
    const [geminiData, setGeminiData] = useState(null);
    const [suggestedPolicy, setSuggestedPolicy] = useState(null);
    const [missingCols, setMissingCols] = useState([]);

    // Filters state
    const [filters, setFilters] = useState({});

    useEffect(() => {
        if (data.length > 0) {
            const conds = POLICY_CONDITIONS[policyType] || {};
            const newFilters = {};
            Object.keys(conds).forEach(col => {
                const config = conds[col];
                if (config.type === 'multiselect') newFilters[col] = config.options;
                else if (config.type === 'multiselect_optional') newFilters[col] = [];
                else if (config.type === 'disability_filter') newFilters[col] = "Any";
                else if (config.type === 'binary') newFilters[col] = config.default;
                else newFilters[col] = config.default || config.max;
            });
            setFilters(newFilters);
            // Don't auto-apply here to avoid loop if applyFilters updates state
        }
    }, [policyType, data.length]);

    const handleUpload = async (e) => {
        if (e) e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('government', file, { policy: policyType });
            setData(res.data);
            setMetrics(res.metrics);
            setSuggestedPolicy(res.optimized_recommendation);
            setMissingCols(res.missing_cols || []);

            const initialFilters = {};
            const conds = POLICY_CONDITIONS[policyType] || {};
            Object.keys(conds).forEach(col => {
                const config = conds[col];
                if (config.type === 'multiselect') initialFilters[col] = config.options;
                else if (config.type === 'multiselect_optional') initialFilters[col] = [];
                else if (config.type === 'disability_filter') initialFilters[col] = "Any";
                else if (config.type === 'binary') initialFilters[col] = config.default;
                else initialFilters[col] = config.default || config.max;
            });
            setFilters(initialFilters);
        } catch (error) {
            console.error("Upload failed", error);
        }
        setLoading(false);
    };

    const handleFilterChange = (feature, value, isMultiSelect = false) => {
        if (isMultiSelect) {
            setFilters(prev => {
                const current = prev[feature] || [];
                const updated = current.includes(value) ? current.filter(v => v !== value) : [...current, value];
                return { ...prev, [feature]: updated };
            });
        } else {
            setFilters(prev => ({ ...prev, [feature]: value }));
        }
    };

    const exportData = (eligible) => {
        const conds = POLICY_CONDITIONS[policyType] || {};
        const filtered = data.filter(row => {
            let isMatch = true;
            Object.keys(conds).forEach(col => {
                const config = conds[col];
                const val = row[col];
                if (config.type === 'max') {
                    if ((parseFloat(val) || 0) > (parseFloat(filters[col]) || config.default)) isMatch = false;
                } else if (config.type === 'min') {
                    if ((parseFloat(val) || 0) < (parseFloat(filters[col]) || config.default)) isMatch = false;
                } else if (config.type === 'multiselect') {
                    const allowed = filters[col] || [];
                    if (!allowed.includes((val || 'unknown').toString())) isMatch = false;
                } else if (config.type === 'disability_filter') {
                    const filterVal = filters[col];
                    const isDis = (val === 1 || val === true || (val || '').toString().toLowerCase() === 'yes');
                    if (filterVal === "Disabled only" && !isDis) isMatch = false;
                    if (filterVal === "Non-disabled only" && isDis) isMatch = false;
                } else if (config.type === 'binary') {
                    if (filters[col]) {
                        if (val === 1 || val === true || (val || '').toString().toLowerCase() === 'yes' || val === '1') isMatch = false;
                    }
                }
            });
            return eligible ? isMatch : !isMatch;
        });

        const filename = `${policyType.replace(' ', '_')}_${eligible ? 'Eligible' : 'Ineligible'}_List.csv`;
        downloadCSV(filtered, filename);
    };


    const applyFilters = async () => {
        setLoading(true);
        try {
            const res = await filterDataset('government', data, filters, { policy: policyType });
            const newMetrics = {
                records_evaluated: res.metrics.records_evaluated,
                eligibility_rate: res.metrics.eligibility_rate,
                eligible: res.metrics.eligible,
                rejected: res.metrics.rejected
            };
            setMetrics(newMetrics);
            setSuggestedPolicy(res.optimized_recommendation);

            const [shapRes, geminiRes] = await Promise.all([
                explainModel('government', data, filters, { policy: policyType }),
                getGeminiSummary('government', { policy: policyType, filters, metrics: newMetrics })
            ]);
            setShapData(shapRes.shap_data);
            setGeminiData(geminiRes);
        } catch (error) {
            console.error("Simulation failed", error);
        }
        setLoading(false);
    };

    return (
        <div className="government-container fade-in">
            {/* Domain Hero */}
            <div className="domain-hero">
                <img src="/assets/government.png" alt="Government Domain" className="domain-hero-img" />
                <div className="domain-hero-content">
                    <h2 className="fw-bold text-primary mb-1">Legislative Impact Simulator</h2>
                    <p className="text-muted mb-0">Modeling public welfare reach and budgetary efficiency across census clusters.</p>
                </div>
            </div>

            <Row>
                {/* Left Sidebar */}
                <Col lg={4} className="mb-4">
                    <div className="filter-panel">
                        {/* Policy Switcher */}
                        <Card className="simulator-card shadow-sm border-0 mb-4 bg-light">
                            <Card.Body className="p-3">
                                <Form.Group>
                                    <Form.Label className="small fw-bold text-muted mb-2">Legislative Program</Form.Label>
                                    <Form.Select 
                                        size="sm" 
                                        value={policyType} 
                                        onChange={(e) => setPolicyType(e.target.value)}
                                        className="rounded-pill border-0 shadow-sm"
                                    >
                                        <option value="scholarship">🎓 Scholarship Program</option>
                                        <option value="pension">👵 Pension Scheme</option>
                                        <option value="housing">🏠 Housing Allotment</option>
                                        <option value="cash_welfare">💰 Cash Welfare Program</option>
                                    </Form.Select>
                                </Form.Group>
                            </Card.Body>
                        </Card>

                        {/* File Upload Card */}
                        {!data.length && (
                            <Card className="simulator-card shadow-sm border-0 mb-4">
                                <Card.Body className="p-4 text-center">
                                    <FaUpload size={40} className="text-primary opacity-25 mb-3" />
                                    <h6 className="fw-bold">Step 1: Load Census Data</h6>
                                    <p className="small text-muted mb-3">Upload your population dataset to begin legislative impact analysis.</p>

                                    <div className="bg-light p-3 rounded-4 mb-4 text-start border border-primary border-opacity-10">
                                        <p className="small fw-bold text-primary mb-2">Required CSV Columns:</p>
                                        <code className="x-small d-block text-muted" style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                                            age, gender, annual_income, education_level, disability_status, family_size, employment_status, owns_house
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
                                        <FaFilter className="me-2" /> Policy Conditions
                                    </h5>
                                </Card.Header>
                                <Card.Body className="px-4 pb-4">
                                    {Object.entries(POLICY_CONDITIONS[policyType] || {}).map(([col, config], idx) => (
                                        <div key={idx} className="mb-4">
                                            {config.type === 'max' || config.type === 'min' ? (
                                                <Form.Group>
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>{config.label}</span>
                                                        <span className="text-primary">{filters[col] !== undefined ? filters[col] : config.default}</span>
                                                    </Form.Label>
                                                    <input type="range" className="form-range" 
                                                        min={config.min} max={config.max} step={config.step}
                                                        value={filters[col] !== undefined ? filters[col] : config.default}
                                                        onChange={(e) => handleFilterChange(col, e.target.value)} />
                                                </Form.Group>
                                            ) : config.type === 'multiselect' || config.type === 'multiselect_optional' ? (
                                                <Form.Group>
                                                    <Form.Label className="small fw-bold mb-2 d-block">{config.label}</Form.Label>
                                                    <div className="bg-light p-2 rounded-3 border-0 shadow-none overflow-auto" style={{ maxHeight: '120px' }}>
                                                        {config.options.map(opt => (
                                                            <Form.Check
                                                                type="checkbox" key={opt} label={opt}
                                                                checked={(filters[col] || []).includes(opt)}
                                                                className="small mb-1"
                                                                onChange={() => handleFilterChange(col, opt, true)}
                                                            />
                                                        ))}
                                                    </div>
                                                </Form.Group>
                                            ) : config.type === 'disability_filter' ? (
                                                <Form.Group>
                                                    <Form.Label className="small fw-bold mb-2">{config.label}</Form.Label>
                                                    <Form.Select size="sm" className="rounded-pill border-0 shadow-sm"
                                                        value={filters[col] || "Any"}
                                                        onChange={(e) => handleFilterChange(col, e.target.value)}
                                                    >
                                                        {config.options.map(o => <option key={o} value={o}>{o}</option>)}
                                                    </Form.Select>
                                                </Form.Group>
                                            ) : config.type === 'binary' ? (
                                                <Form.Check
                                                    type="switch" label={config.label} checked={!!filters[col]} className="small fw-bold"
                                                    onChange={(e) => handleFilterChange(col, e.target.checked)}
                                                />
                                            ) : null}
                                        </div>
                                    ))}

                                    <Button onClick={applyFilters} className="btn-premium w-100 py-2 shadow-sm rounded-pill mt-2" disabled={loading}>
                                        {loading ? <Spinner size="sm" /> : 'Simulate Legislation'}
                                    </Button>

                                    {suggestedPolicy && Object.keys(suggestedPolicy.rule).length > 0 && (
                                        <div className="mt-4 p-3 bg-light rounded-4 border border-info border-dashed">
                                            <h6 className="text-info small fw-bold mb-2">⭐ ML Optimization Focus</h6>
                                            <p className="small text-muted mb-2 font-italic">Projected reach: {(suggestedPolicy.rate * 100).toFixed(1)}%</p>
                                            <div className="small text-muted ps-2 border-start border-info border-2">
                                                {Object.entries(suggestedPolicy.rule).map(([k, v]) => (
                                                    <div key={k} className="mb-1">
                                                        <b className="text-capitalize">{k.replace(/_/g, ' ')}</b>: {v}
                                                    </div>
                                                ))}
                                            </div>
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
                            {missingCols.length > 0 && (
                                <Card className="simulator-card bg-warning bg-opacity-10 border-warning mb-4 shadow-none">
                                    <Card.Body className="py-2 px-3 small">
                                        ⚠️ <strong>Data Inconsistency:</strong> Missing features: {missingCols.join(', ')}. Matching logic adjusted.
                                    </Card.Body>
                                </Card>
                            )}

                            <Row className="g-3 mb-4">
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm">
                                        <small className="text-muted d-block mb-1">Census Volume</small>
                                        <h4 className="fw-bold mb-0">{metrics.records_evaluated}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-success border-4">
                                        <small className="text-muted d-block mb-1">Eligible Citizens</small>
                                        <h4 className="fw-bold mb-0 text-success">{metrics.eligible}</h4>
                                    </Card>
                                </Col>
                                <Col sm={4}>
                                    <Card className="simulator-card text-center p-3 border-0 bg-white shadow-sm border-start border-danger border-4">
                                        <small className="text-muted d-block mb-1">Budgetary Savings</small>
                                        <h4 className="fw-bold mb-0 text-danger">{metrics.rejected}</h4>
                                    </Card>
                                </Col>
                            </Row>

                            <Card className="simulator-card border-0 mb-4 overflow-hidden shadow-sm">
                                <Card.Header className="bg-white border-bottom-0 pt-4 px-4 d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0"><FaChartBar className="me-2 text-info" /> Public Welfare Reach</h5>
                                    <div className="metric-badge bg-primary bg-opacity-10 text-primary">
                                        Impact Rate: {(metrics.eligibility_rate * 100).toFixed(1)}%
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
                                                { name: 'Filtered', count: metrics.rejected, fill: '#e74c3c' }
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
                                        <h5 className="mb-0 fs-5 fw-bold"><FaRobot className="me-2" /> Legislative Strategic Summary</h5>
                                        <Button variant="outline-light" size="sm" className="rounded-pill px-3 py-1" onClick={() => generatePolicyReport('government', metrics, filters, geminiData)}>
                                            <FaDownload className="me-1 small" /> Export Brief
                                        </Button>
                                    </div>
                                    
                                    {geminiData && geminiData.scenarios ? (
                                        <div className="bg-white rounded-4 p-1 overflow-hidden shadow-sm mb-4">
                                            <div className="table-responsive">
                                                <Table hover className="mb-0 align-middle border-0">
                                                    <thead className="bg-light">
                                                        <tr className="border-0">
                                                            <th className="py-3 ps-4 border-0 text-dark small fw-bold">Scenario</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold">Strategic Aim</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold">Public Impact</th>
                                                            <th className="py-3 border-0 text-dark small fw-bold pe-4">Fiscal Control</th>
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
                                            <p className="mb-0 small">{loading ? 'Synthesizing legislative impact...' : 'Apply legislation to generate Gemini Statutory Review'}</p>
                                        </div>
                                    )}

                                    {geminiData && geminiData.overall_summary && (
                                        <div className="p-3 bg-white bg-opacity-10 rounded-4 border border-white border-opacity-10">
                                            <h6 className="fw-bold mb-2 small text-uppercase tracking-wider">Executive Statutory Brief:</h6>
                                            <p className="mb-0 small opacity-90" style={{ lineHeight: '1.6' }}>{geminiData.overall_summary}</p>
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>

                            {/* SHAP Insights */}
                            {shapData && shapData.length > 0 && (
                                <Card className="simulator-card border-0 mb-4 shadow-sm">
                                    <Card.Header className="bg-white border-bottom-0 pt-4 px-4">
                                        <h5 className="mb-0"><FaChartLine className="me-2 text-warning" /> Demographic Impact Indicators (SHAP)</h5>
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
                            <FaLandmark size={80} className="text-light mb-4" />
                            <h3 className="text-muted">Legislative Simulator Ready</h3>
                            <p className="text-muted">Upload census application data to begin analyzing public policy impacts.</p>
                        </div>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default Government;
