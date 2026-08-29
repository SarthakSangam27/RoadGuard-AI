function Navbar() {
  return (
    <nav className="rg-navbar">
      <div className="rg-brand">
        <span className="rg-brand-dot" />

        <span>
          Road
          <span className="rg-brand-highlight">Guard-AI</span>
        </span>
      </div>

      <div className="rg-nav-links">
        <a href="#scan" className="active">
          Scan
        </a>
        
        
        <a href="#history">
          Scan History
        </a>

        <a href="#performance">
          Model Performance
        </a>

        <a href="#analytics">
          Analytics
        </a>

        <a href="#docs">
          Docs
        </a>
      </div>
    </nav>
  );
}

export default Navbar;