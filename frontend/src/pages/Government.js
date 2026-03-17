import React, { useState } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table, ProgressBar } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaLandmark } from 'react-icons/fa';

const Government = () => {
    const [file, setFile] = useState(null);
    const [policyType, setPolicyType] = useState('scholarship');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [shapData, setShapData] = useState([]);
    const [geminiSummary, setGeminiSummary] = useState('');
    const [suggestedPolicy, setSuggestedPolicy] = useState(null);
    const [scenario, setScenario] = useState('Eligible Segment');
    const [availableCols, setAvailableCols] = useState([]);
    const [missingCols, setMissingCols] = useState([]);

    // Filters state
    const [filters, setFilters] = useState({});

    // Re-run analysis if policy type changes and we have data
    React.useEffect(() => {
        if (data.length > 0) {
            // Reset filters to defaults for the new policy
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
            applyFilters();
        }
    }, [policyType]);

    const POLICY_CONDITIONS = {
        scholarship: {
            annual_income: { type: "max", label: "Max Annual Income (₹)", default: 200000, min: 10000, max: 500000, step: 5000 },
            education_level: { type: "multiselect", label: "Eligible Education Levels", options: ["UG", "PG", "Diploma", "12th", "10th", "unknown"] },
            disability_status: { type: "disability_filter", label: "Disability Status", options: ["Any", "Disabled only", "Non-disabled only"] },
            gender: { type: "multiselect_optional", label: "Gender (optional)", options: ["Male", "Female", "Other", "unknown"] },
        },
        pension: {
            age: { type: "min", label: "Minimum Age", default: 58, min: 40, max: 85, step: 1 },
            employment_status: { type: "multiselect", label: "Eligible Employment Status", options: ["Employed", "Unemployed", "Self-Employed", "Student", "Retired", "unknown"] },
            annual_income: { type: "max", label: "Max Annual Income (₹)", default: 150000, min: 20000, max: 500000, step: 5000 },
        },
        housing: {
            annual_income: { type: "max", label: "Max Annual Income (₹)", default: 300000, min: 50000, max: 600000, step: 10000 },
            family_size: { type: "min", label: "Min Family Size", default: 2, min: 1, max: 8, step: 1 },
            employment_status: { type: "multiselect", label: "Eligible Employment Status", options: ["Employed", "Unemployed", "Self-Employed", "Student", "unknown"] },
            owns_house: { type: "binary", label: "Must NOT own house", default: true },
        },
        cash_welfare: {
            annual_income: { type: "max", label: "Max Annual Income (₹)", default: 150000, min: 10000, max: 400000, step: 5000 },
            family_size: { type: "min", label: "Min Family Size", default: 2, min: 1, max: 10, step: 1 },
            disability_status: { type: "disability_filter", label: "Disability Status", options: ["Any", "Disabled only", "Non-disabled only"] },
            age: { type: "min", label: "Minimum Age", default: 18, min: 0, max: 100, step: 1 },
            education_level: { type: "multiselect", label: "Eligible Education Levels", options: ["UG", "PG", "Diploma", "12th", "10th", "unknown"] },
            owns_house: { type: "binary", label: "Must NOT own house", default: true },
            gender: { type: "multiselect_optional", label: "Gender (optional)", options: ["Male", "Female", "Other", "unknown"] },
        },
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('government', file, { policy: policyType });
            setData(res.data);
            setMetrics(res.metrics);
            setSuggestedPolicy(res.optimized_recommendation);
            setAvailableCols(res.available_cols || []);
            setMissingCols(res.missing_cols || []);

            // Setup default filters based on POLICY_CONDITIONS
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

            // Auto fetch SHAP
            explainModel('government', data, filters, { policy: policyType })
                .then(shapRes => setShapData(shapRes.shap_data))
                .catch(err => console.error(err));

            // Auto fetch Gemini
            fetchSummary(filters, newMetrics);
        } catch (error) {
            console.error("Filter failed", error);
        }
        setLoading(false);
    };

    const fetchExplanation = async () => {
        setLoading(true);
        try {
            const res = await explainModel('government', data, filters, { policy: policyType });
            setShapData(res.shap_data);
        } catch (error) {
            console.error("Explain failed", error);
        }
        setLoading(false);
    };

    const fetchSummary = async (currentFilters = filters, currentMetrics = metrics) => {
        setLoading(true);
        try {
            const res = await getGeminiSummary('government', { 
                policy: policyType,
                scenario: scenario,
                filters: currentFilters,
                metrics: currentMetrics
            });
            setGeminiSummary(res.explanation);
        } catch (error) {
            console.error("Summary failed", error);
        }
        setLoading(false);
    };

    return (
        <div className="gov-dashboard fade-in">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2><FaLandmark className="text-info me-2" /> Government Policy Simulator</h2>
                <Form.Select style={{ width: '250px' }} value={policyType} onChange={e => setPolicyType(e.target.value)}>
                    <option value="scholarship">Scholarship Program</option>
                    <option value="pension">Pension Scheme</option>
                    <option value="housing">Housing Allotment</option>
                    <option value="cash_welfare">Cash Welfare</option>
                </Form.Select>
            </div>

            {/* Upload Section */}
            {!data.length && (
                <Card className="glass-card mb-4 text-center p-5">
                    <Card.Body>
                        <FaUpload size={40} className="text-primary mb-3" />
                        <h4>Upload Census / Application Dataset</h4>
                        <p className="text-muted">Upload citizen records to simulate public welfare eligibility and calculate budgetary impact.</p>
                        <Form onSubmit={handleUpload} className="d-flex justify-content-center">
                            <Form.Control type="file" onChange={e => setFile(e.target.files[0])} style={{ maxWidth: '300px' }} className="me-2" />
                            <Button type="submit" variant="primary" disabled={loading || !file}>
                                {loading ? <Spinner animation="border" size="sm" /> : 'Run Policy Simulation'}
                            </Button>
                        </Form>
                    </Card.Body>
                </Card>
            )}

            {/* Main Interactive Dashboard */}
            {data.length > 0 && (
                <>
                    {/* Top Metrics Cards */}
                    {metrics && (
                        <Row className="mb-4">
                            <Col md={4}>
                                <Card className="glass-card text-center border-left-primary">
                                    <Card.Body>
                                        <h6 className="text-muted text-uppercase">Total Persons Evaluated</h6>
                                        <h2 className="mb-0">{metrics.records_evaluated}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4}>
                                <Card className="glass-card text-center border-left-success">
                                    <Card.Body>
                                        <h6 className="text-muted text-uppercase">Eligible Total</h6>
                                        <h2 className="text-success mb-0">{metrics.eligible}</h2>
                                        <small className="text-muted">{(metrics.eligibility_rate * 100).toFixed(1)}% of total</small>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4}>
                                <Card className="glass-card text-center border-left-danger">
                                    <Card.Body>
                                        <h6 className="text-muted text-uppercase">Total Rejection</h6>
                                        <h2 className="text-danger mb-0">{metrics.rejected}</h2>
                                        <small className="text-muted">{((1 - metrics.eligibility_rate) * 100).toFixed(1)}% of total</small>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    )}

                    {missingCols.length > 0 && (
                        <div className="alert alert-warning mb-4">
                            ⚠️ <strong>Missing Columns:</strong> The dataset is missing certain required columns for this policy filter: <b>{missingCols.join(', ')}</b>. Matching rules will be ignored.
                        </div>
                    )}
                    <Row>
                        {/* Filters Panel */}
                        <Col md={4}>
                            <Card className="glass-card mb-4">
                                <Card.Header className="bg-transparent border-0 pt-4 pb-0">
                                    <h5 className="mb-0"><FaFilter className="me-2 text-primary" /> Statutory Thresholds</h5>
                                </Card.Header>
                                <Card.Body>
                                    {Object.entries(POLICY_CONDITIONS[policyType] || {}).map(([col, config], idx) => {
                                        if (config.type === 'max' || config.type === 'min') {
                                            return (
                                                <Form.Group className="mb-3" key={idx}>
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>{config.label}</span>
                                                        <span className="text-primary">{filters[col] !== undefined ? filters[col] : config.default}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={config.min} max={config.max} step={config.step}
                                                        value={filters[col] !== undefined ? filters[col] : config.default}
                                                        onChange={(e) => handleFilterChange(col, e.target.value)}
                                                    />
                                                </Form.Group>
                                            );
                                        } else if (config.type === 'multiselect' || config.type === 'multiselect_optional') {
                                            return (
                                                <Form.Group className="mb-3" key={idx}>
                                                    <Form.Label className="small fw-bold">{config.label}</Form.Label>
                                                    <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
                                                        {config.options.map(opt => (
                                                            <Form.Check
                                                                type="checkbox" key={opt} label={opt}
                                                                checked={(filters[col] || []).includes(opt)}
                                                                onChange={() => handleFilterChange(col, opt, true)}
                                                            />
                                                        ))}
                                                    </div>
                                                </Form.Group>
                                            );
                                        } else if (config.type === 'disability_filter') {
                                            return (
                                                <Form.Group className="mb-3" key={idx}>
                                                    <Form.Label className="small fw-bold">{config.label}</Form.Label>
                                                    <Form.Select
                                                        value={filters[col] || "Any"}
                                                        onChange={(e) => handleFilterChange(col, e.target.value)}
                                                    >
                                                        {config.options.map(o => <option key={o} value={o}>{o}</option>)}
                                                    </Form.Select>
                                                </Form.Group>
                                            );
                                        } else if (config.type === 'binary') {
                                            return (
                                                <Form.Group className="mb-3" key={idx}>
                                                    <Form.Check
                                                        type="switch" label={config.label}
                                                        checked={!!filters[col]}
                                                        onChange={(e) => handleFilterChange(col, e.target.checked)}
                                                    />
                                                </Form.Group>
                                            );
                                        }
                                        return null;
                                    })}

                                    <Button variant="outline-primary" className="w-100 mt-2" onClick={applyFilters} disabled={loading}>
                                        {loading ? 'Recalculating...' : 'Apply Legislation'}
                                    </Button>

                                    {suggestedPolicy && Object.keys(suggestedPolicy.rule).length > 0 && (
                                        <div className="mt-4 p-3 bg-light rounded border border-info">
                                            <h6 className="text-info mb-2">⭐ ML Optimized Thresholds</h6>
                                            <p className="small mb-2">AI suggests the following thresholds to balance budget and reach (Est Rate: {(suggestedPolicy.rate * 100).toFixed(1)}%):</p>
                                            <ul className="small mb-0 mt-1">
                                                {Object.entries(suggestedPolicy.rule).map(([k, v]) => (
                                                    <li key={k}><b>{k.replace('_', ' ')}</b> limit: {v}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>
                        </Col>

                        {/* Explainable AI & SHAP Panel */}
                        <Col md={8}>
                            <Card className="glass-card mb-4 min-vh-50">
                                <Card.Body>
                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                        <h5><FaChartBar className="me-2 text-primary" /> Demographic Impact Drivers (SHAP)</h5>
                                    </div>

                                    {shapData.length > 0 ? (
                                        <div style={{ height: '300px' }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={shapData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                                                    <XAxis type="number" hide />
                                                    <YAxis dataKey="feature" type="category" axisLine={false} tickLine={false} width={100} />
                                                    <Tooltip cursor={{ fill: 'transparent' }} />
                                                    <Bar dataKey="importance" fill="var(--primary-color)" radius={[0, 4, 4, 0]} barSize={20} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    ) : (
                                        <div className="text-center text-muted p-5 bg-light rounded" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            Adjust thresholds and apply to automatically run SHAP impact calculations.
                                        </div>
                                    )}
                                </Card.Body>
                            </Card>

                            {/* Gemini Summary Section */}
                            <Card className="glass-card bg-primary text-white">
                                <Card.Body>
                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                        <h5 className="mb-0"><FaRobot className="me-2" /> Gemini AI Legislative Brief</h5>
                                        <Form.Select size="sm" style={{ width: '180px' }} value={scenario} onChange={e => { setScenario(e.target.value); setTimeout(() => fetchSummary(), 100); }}>
                                            <option value="Eligible Segment">Eligible Segment</option>
                                            <option value="Ineligible Segment">Ineligible Segment</option>
                                            <option value="Overall Impact">Overall Impact</option>
                                        </Form.Select>
                                    </div>
                                    {geminiSummary ? (
                                        <p className="mb-0 lh-lg" style={{ opacity: 0.9 }}>{geminiSummary}</p>
                                    ) : (
                                        <p className="mb-0 text-white-50 small">No brief generated yet. Click to synthesize a policy summary for legislative review.</p>
                                    )}
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </>
            )}
        </div>
    );
};

export default Government;
