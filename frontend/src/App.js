import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Layout from './components/Layout';

// Placeholder Pages
const Home = () => (
    <div className="text-center mt-5">
        <h1 className="display-4 fw-bold text-gradient mb-4">AI Policy Impact Simulator</h1>
        <p className="lead text-muted max-w-50 mx-auto">
            Upload compliance datasets, adjust legislative thresholds, and see AI-driven impacts instantly across Insurance, Human Resources, and Government domains.
        </p>
    </div>
);
import Insurance from './pages/Insurance';

import HR from './pages/HR';

import Government from './pages/Government';

function App() {
    return (
        <Router>
            <Layout>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/insurance" element={<Insurance />} />
                    <Route path="/hr" element={<HR />} />
                    <Route path="/government" element={<Government />} />
                </Routes>
            </Layout>
        </Router>
    );
}

export default App;
