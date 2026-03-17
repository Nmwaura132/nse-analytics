import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import DataScience from './pages/DataScience';

function App() {
    const [searchQuery, setSearchQuery] = useState("");

    return (
        <Router>
            <div className="app-container">
                <Navbar searchQuery={searchQuery} setSearchQuery={setSearchQuery} />
                <main className="content">
                    <Routes>
                        <Route path="/" element={<Dashboard searchQuery={searchQuery} />} />
                        <Route path="/portfolio" element={<Portfolio />} />
                        <Route path="/datascience" element={<DataScience />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
