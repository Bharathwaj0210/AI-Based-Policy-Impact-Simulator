import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Layout from './components/Layout';
import Insurance from './pages/Insurance';
import HR from './pages/HR';
import Government from './pages/Government';
import Home from './pages/Home';

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
