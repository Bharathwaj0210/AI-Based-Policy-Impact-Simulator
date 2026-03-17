import React, { useState } from 'react';
import { uploadDataset, filterDataset, explainModel, getGeminiSummary } from '../api/api';
import { Form, Button, Row, Col, Card, Spinner, Table, ProgressBar } from 'react-bootstrap';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { FaUpload, FaRobot, FaFilter, FaChartBar, FaShieldAlt } from 'react-icons/fa';

const Insurance = () => {
    const [file, setFile] = useState(null);
    const [insuranceType, setInsuranceType] = useState('Health Insurance');
    const [loading, setLoading] = useState(false);

    // State
    const [data, setData] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [summaryStats, setSummaryStats] = useState([]);
    const [shapData, setShapData] = useState([]);
    const [geminiSummary, setGeminiSummary] = useState('');
    const [recommendations, setRecommendations] = useState([]);
    const [scenario, setScenario] = useState('Average Case');

    // Filters state
    const [filters, setFilters] = useState({});

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;
        setLoading(true);
        try {
            const res = await uploadDataset('insurance', file, { insurance_type: insuranceType });
            setData(res.data);
            setMetrics(res.overall_metrics);
            setSummaryStats(res.summary);
            setRecommendations(res.recommendations || []);
            // Default filters based on Streamlit defaults
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

            // Auto fetch SHAP
            explainModel('insurance', data, filters, { insurance_type: insuranceType })
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
            const res = await explainModel('insurance', data, filters, { insurance_type: insuranceType });
            setShapData(res.shap_data);
        } catch (error) {
            console.error("Explain failed", error);
        }
        setLoading(false);
    };

    const fetchSummary = async (currentFilters = filters, currentMetrics = metrics) => {
        setLoading(true);
        try {
            const res = await getGeminiSummary('insurance', { 
                insurance_type: insuranceType,
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
        <div className="insurance-dashboard fade-in">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2><FaShieldAlt className="text-success me-2" /> Insurance Domain Simulator</h2>
                <Form.Select style={{ width: '250px' }} value={insuranceType} onChange={e => setInsuranceType(e.target.value)}>
                    <option value="Health Insurance">Health Insurance</option>
                    <option value="Vehicle Insurance">Vehicle Insurance</option>
                </Form.Select>
            </div>

            {/* Upload Section */}
            {!data.length && (
                <Card className="glass-card mb-4 text-center p-5">
                    <Card.Body>
                        <FaUpload size={40} className="text-primary mb-3" />
                        <h4>Upload Dataset</h4>
                        <p className="text-muted">Upload a complete CSV dataset containing the required policyholder demographic features to begin the simulation.</p>
                        <Form onSubmit={handleUpload} className="d-flex justify-content-center">
                            <Form.Control type="file" onChange={e => setFile(e.target.files[0])} style={{ maxWidth: '300px' }} className="me-2" />
                            <Button type="submit" variant="primary" disabled={loading || !file}>
                                {loading ? <Spinner animation="border" size="sm" /> : 'Analyze Dataset'}
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

                    <Row>
                        {/* Filters Panel */}
                        <Col md={4}>
                            <Card className="glass-card mb-4">
                                <Card.Header className="bg-transparent border-0 pt-4 pb-0">
                                    <h5 className="mb-0"><FaFilter className="me-2 text-primary" /> Policy Constraints</h5>
                                </Card.Header>
                                <Card.Body>
                                    {insuranceType === 'Health Insurance' ? (
                                        <>
                                            <Form.Group className="mb-3">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    <span>Max Age</span>
                                                    <span className="text-primary">{filters.max_age !== undefined ? filters.max_age : 60}</span>
                                                </Form.Label>
                                                <Form.Range
                                                    min={18} max={80} step={1}
                                                    value={filters.max_age !== undefined ? filters.max_age : 60}
                                                    onChange={(e) => handleFilterChange('max_age', e.target.value)}
                                                />
                                            </Form.Group>
                                            <Form.Group className="mb-3">
                                                <Form.Label className="d-flex justify-content-between small fw-bold">
                                                    <span>Max BMI</span>
                                                    <span className="text-primary">{filters.max_bmi !== undefined ? filters.max_bmi : 35.0}</span>
                                                </Form.Label>
                                                <Form.Range
                                                    min={18.0} max={50.0} step={0.1}
                                                    value={filters.max_bmi !== undefined ? filters.max_bmi : 35.0}
                                                    onChange={(e) => handleFilterChange('max_bmi', e.target.value)}
                                                />
                                            </Form.Group>
                                            <Form.Group className="mb-3">
                                                <Form.Label className="small fw-bold">Allow Smokers?</Form.Label>
                                                <Form.Select
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
                                            <div className="mb-3 p-2 bg-light rounded border-start border-primary border-4">
                                                <small className="text-primary fw-bold d-block mb-2 text-uppercase">Necessary Conditions</small>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Max Vehicle Age</span>
                                                        <span className="text-primary">{filters.max_vehicle_age !== undefined ? filters.max_vehicle_age : 15}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={0} max={30} step={1}
                                                        value={filters.max_vehicle_age !== undefined ? filters.max_vehicle_age : 15}
                                                        onChange={(e) => handleFilterChange('max_vehicle_age', e.target.value)}
                                                    />
                                                </Form.Group>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Min Experience (Yrs)</span>
                                                        <span className="text-primary">{filters.min_experience !== undefined ? filters.min_experience : 2}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={0} max={50} step={1}
                                                        value={filters.min_experience !== undefined ? filters.min_experience : 2}
                                                        onChange={(e) => handleFilterChange('min_experience', e.target.value)}
                                                    />
                                                </Form.Group>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Max Customer Age</span>
                                                        <span className="text-primary">{filters.max_customer_age !== undefined ? filters.max_customer_age : 70}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={18} max={100} step={1}
                                                        value={filters.max_customer_age !== undefined ? filters.max_customer_age : 70}
                                                        onChange={(e) => handleFilterChange('max_customer_age', e.target.value)}
                                                    />
                                                </Form.Group>
                                            </div>

                                            <div className="mb-3 p-2 bg-light rounded border-start border-warning border-4">
                                                <small className="text-warning fw-bold d-block mb-2 text-uppercase">Balance Conditions (Optional)</small>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Max Vehicle Value ($)</span>
                                                        <span className="text-warning">{filters.max_value_vehicle || 50000}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={1000} max={100000} step={500}
                                                        value={filters.max_value_vehicle || 50000}
                                                        onChange={(e) => handleFilterChange('max_value_vehicle', e.target.value)}
                                                    />
                                                </Form.Group>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Max Cylinder Capacity</span>
                                                        <span className="text-warning">{filters.max_cylinder_capacity || 2500}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={500} max={6000} step={100}
                                                        value={filters.max_cylinder_capacity || 2500}
                                                        onChange={(e) => handleFilterChange('max_cylinder_capacity', e.target.value)}
                                                    />
                                                </Form.Group>
                                                <Form.Group className="mb-2">
                                                    <Form.Label className="d-flex justify-content-between small fw-bold">
                                                        <span>Max Premium ($)</span>
                                                        <span className="text-warning">{filters.max_premium || 1000}</span>
                                                    </Form.Label>
                                                    <Form.Range
                                                        min={100} max={5000} step={50}
                                                        value={filters.max_premium || 1000}
                                                        onChange={(e) => handleFilterChange('max_premium', e.target.value)}
                                                    />
                                                </Form.Group>
                                            </div>
                                        </>
                                    )}

                                    <Button variant="outline-primary" className="w-100 mt-2" onClick={applyFilters} disabled={loading}>
                                        {loading ? 'Recalculating...' : 'Apply Thresholds'}
                                    </Button>

                                    {recommendations.length > 0 && (
                                        <div className="mt-4 p-3 bg-light rounded border border-success">
                                            <h6 className="text-success mb-2">⭐ ML Policy Recommendation</h6>
                                            <ul className="small mb-0">
                                                {recommendations.map((r, i) => (
                                                    <li key={i}>{r}</li>
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
                                        <h5 className="mb-0"><FaRobot className="me-2" /> Gemini AI Executive Summary</h5>
                                        <Form.Select size="sm" style={{ width: '150px' }} value={scenario} onChange={e => { setScenario(e.target.value); setTimeout(() => fetchSummary(), 100); }}>
                                            <option value="Best Case">Best Case</option>
                                            <option value="Average Case">Average Case</option>
                                            <option value="Worst Case">Worst Case</option>
                                        </Form.Select>
                                    </div>
                                    {geminiSummary ? (
                                        <p className="mb-0 lh-lg" style={{ opacity: 0.9 }}>{geminiSummary}</p>
                                    ) : (
                                        <p className="mb-0 text-white-50 small">No summary generated yet. Click above to request a comprehensive natural language analysis of the current policy metrics.</p>
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

export default Insurance;
