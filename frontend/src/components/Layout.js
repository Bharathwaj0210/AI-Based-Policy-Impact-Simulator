import React from 'react';
import TopNav from './TopNav';

const Layout = ({ children }) => {
    return (
        <div className="layout-wrapper bg-light min-vh-100">
            <TopNav />
            <main className="container-fluid p-4 fade-in">
                {children}
            </main>
        </div>
    );
};

export default Layout;
