import React from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import Insurance from './pages/Insurance';
import Government from './pages/Government';
import HR from './pages/HR';

function App() {
    return (
        <div className="App" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Header />
            <main style={{ padding: '1rem' }}>
                <Insurance />
                <Government />
                <HR />
            </main>
            <Footer />
        </div>
    );
}

export default App;
