import React, { useState } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table, ProgressBar } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaUserTie } from 'react-icons/fa';

const HR = () => {
    const [file, setFile] = useState(null);
    const [hrType, setHrType] = useState('Recruitment Optimization');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [summaryStats, setSummaryStats] = useState([]);
    const [shapData, setShapData] = useState([]);
    const [geminiSummary, setGeminiSummary] = useState('');
    const [suggestedPolicy, setSuggestedPolicy] = useState(null);
    const [scenario, setScenario] = useState('Average Case');

    // Filters state
    const [filters, setFilters] = useState({});

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('hr', file, { analysis_type: hrType });
            setData(res.data);
            setMetrics(res.overall_metrics);
            setSummaryStats(res.summary);
            setSuggestedPolicy(res.suggested_policy || res.recommendation);
            // Default filters based on summary stats
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

            // Auto fetch SHAP
            explainModel('hr', data, filters, { analysis_type: hrType })
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
            const res = await explainModel('hr', data, filters, { analysis_type: hrType });
            setShapData(res.shap_data);
        } catch (error) {
            console.error("Explain failed", error);
        }
        setLoading(false);
    };

    const fetchSummary = async (currentFilters = filters, currentMetrics = metrics) => {
        setLoading(true);
        try {
            // Compute mean of displayed subset for Gemini
            const summary_data = {};
            if (data.length > 0) {
                const caseData = data.filter(d => d.case_type === scenario);
                if (caseData.length > 0) {
                    ['age', 'tenureyears', 'performance score', 'current employee rating', 'isactive'].forEach(f => {
                        const sum = caseData.reduce((acc, val) => acc + (parseFloat(val[f]) || 0), 0);
                        summary_data[f] = (sum / caseData.length).toFixed(2);
                    });
                }
            }
            const res = await getGeminiSummary('hr', { 
                analysis_type: hrType, 
                scenario: scenario, 
                summary_data: summary_data,
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
        <div className="hr-dashboard fade-in">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2><FaUserTie className="text-warning me-2" /> HR Domain Simulator</h2>
                <Form.Select style={{ width: '250px' }} value={hrType} onChange={e => setHrType(e.target.value)}>
                    <option value="Recruitment Optimization">Recruitment Optimization</option>
                    <option value="Attrition Prediction">Attrition Prediction</option>
                </Form.Select>
            </div>

            {/* Upload Section */}
            {!data.length && (
                <Card className="glass-card mb-4 text-center p-5">
                    <Card.Body>
                        <FaUpload size={40} className="text-primary mb-3" />
                        <h4>Upload HR Dataset</h4>
                        <p className="text-muted">Upload employee or candidate records to simulate optimized HR policies.</p>
                        <Form onSubmit={handleUpload} className="d-flex justify-content-center">
                            <Form.Control type="file" onChange={e => setFile(e.target.files[0])} style={{ maxWidth: '300px' }} className="me-2" />
                            <Button type="submit" variant="primary" disabled={loading || !file}>
                                {loading ? <Spinner animation="border" size="sm" /> : 'Run Analysis'}
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
                                        <h2 className="mb-0">{metrics.records_evaluated || metrics.total_records}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4}>
                                <Card className="glass-card text-center border-left-success">
                                    <Card.Body>
                                        <h6 className="text-muted text-uppercase">Eligible Total</h6>
                                        <h2 className="text-success mb-0">{metrics.eligible || metrics.best_case}</h2>
                                        <small className="text-muted">{((metrics.eligibility_rate || 0) * 100).toFixed(1)}% of total</small>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={4}>
                                <Card className="glass-card text-center border-left-danger">
                                    <Card.Body>
                                        <h6 className="text-muted text-uppercase">Total Rejection</h6>
                                        <h2 className="text-danger mb-0">{metrics.rejected || metrics.worst_case}</h2>
                                        <small className="text-muted">{((1 - (metrics.eligibility_rate || 0)) * 100).toFixed(1)}% of total</small>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    )}

                    <Row>
                        {/* Filters Panel */}
                        <Col md={4}>
                            <Card className="glass-card mb-4">
                                <Card.Header className="bg-transparent border-0 pt-4 pb-0">
                                    <h5 className="mb-0"><FaFilter className="me-2 text-primary" /> Policy Constraints</h5>
                                </Card.Header>
                                <Card.Body>
                                    <Form.Group className="mb-3">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            <span>Minimum Age</span>
                                            <span className="text-primary">{filters.age_min || 18}</span>
                                        </Form.Label>
                                        <Form.Range
                                            min={18} max={65} step={1}
                                            value={filters.age_min || 18}
                                            onChange={(e) => handleFilterChange('age_min', e.target.value)}
                                        />
                                    </Form.Group>
                                    <Form.Group className="mb-3">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            <span>Minimum Rating</span>
                                            <span className="text-primary">{filters.rating_min || 1}</span>
                                        </Form.Label>
                                        <Form.Range
                                            min={1} max={5} step={1}
                                            value={filters.rating_min || 1}
                                            onChange={(e) => handleFilterChange('rating_min', e.target.value)}
                                        />
                                    </Form.Group>
                                    <Form.Group className="mb-3">
                                        <Form.Label className="d-flex justify-content-between small fw-bold">
                                            <span>Minimum Tenure</span>
                                            <span className="text-primary">{filters.tenure_min || 0}</span>
                                        </Form.Label>
                                        <Form.Range
                                            min={0} max={20} step={1}
                                            value={filters.tenure_min || 0}
                                            onChange={(e) => handleFilterChange('tenure_min', e.target.value)}
                                        />
                                    </Form.Group>

                                    <Button variant="outline-primary" className="w-100 mt-2" onClick={applyFilters} disabled={loading}>
                                        {loading ? 'Recalculating...' : 'Apply Thresholds'}
                                    </Button>

                                    {suggestedPolicy && (
                                        <div className="mt-4 p-3 bg-light rounded border border-warning">
                                            <h6 className="text-warning mb-2">⭐ Suggested Optimum Strategy</h6>
                                            {Array.isArray(suggestedPolicy) ? (
                                                <ul className="small mb-0">
                                                    {suggestedPolicy.map((item, i) => <li key={i}>{item}</li>)}
                                                </ul>
                                            ) : (typeof suggestedPolicy === 'object' && suggestedPolicy !== null) ? (
                                                <>
                                                    <p className="small mb-0">For minimum risk, focus on:</p>
                                                    <ul className="small mb-0 mt-1">
                                                        {Object.entries(suggestedPolicy).map(([k, v]) => (
                                                            <li key={k}><b>{k.replace(/_/g, ' ')}</b>: {v}</li>
                                                        ))}
                                                    </ul>
                                                </>
                                            ) : (
                                                <p className="small mb-0">{suggestedPolicy}</p>
                                            )}
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
                                        <h5><FaChartBar className="me-2 text-primary" /> AI Decision Drivers (SHAP)</h5>
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
                                        <h5 className="mb-0"><FaRobot className="me-2" /> Gemini AI HR Summary</h5>
                                        <div className="d-flex align-items-center">
                                            <Form.Select size="sm" className="me-2" style={{ width: '150px' }} value={scenario} onChange={e => { setScenario(e.target.value); setTimeout(() => fetchSummary(), 100); }}>
                                                <option value="Best Case">Best Case</option>
                                                <option value="Average Case">Average Case</option>
                                                <option value="Worst Case">Worst Case</option>
                                            </Form.Select>
                                        </div>
                                    </div>
                                    {geminiSummary ? (
                                        <p className="mb-0 lh-lg" style={{ opacity: 0.9 }}>{geminiSummary}</p>
                                    ) : (
                                        <p className="mb-0 text-white-50 small">No summary generated yet. Click above to request a comprehensive natural language analysis of the current HR policy metrics.</p>
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

export default HR;
