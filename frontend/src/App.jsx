import "./App.css";

import Navbar from "./components/layout/Navbar";
import Hero from "./components/hero/Hero";
import Dashboard from "./pages/Dashboard";
import PerformanceSection from "./components/performance/PerformanceSection";
import DocsSection from "./components/docs/DocsSection";
import ScanHistory from "./components/history/ScanHistory";
import AnalyticsDashboard from "./components/analytics/AnalyticsDashboard";
function App() {
  return (
    <div className="roadguard-app">
      <Navbar />

      <Hero />

      <Dashboard />

      <PerformanceSection />

      <DocsSection />

      <ScanHistory />

      <AnalyticsDashboard />
      </div>
  );
}

export default App;
