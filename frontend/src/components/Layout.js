import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
    return (
        <div className="d-flex" style={{ overflowX: 'hidden' }}>
            <Sidebar />
            <div className="flex-grow-1 bg-light position-relative" style={{ minHeight: '100vh', overflowY: 'auto' }}>
                <div className="container-fluid p-4 fade-in">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Layout;
