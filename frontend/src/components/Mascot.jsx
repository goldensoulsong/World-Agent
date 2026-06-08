import React from 'react';

function Mascot({ agentState }) {
  return (
    <div id="ai-mascot" className={`mascot-book ${agentState}`} title="Nexus Core">
      <svg viewBox="0 0 100 100" className="mascot-svg">
        {/* Book Pages */}
        <path d="M 50 80 Q 25 90 10 75 L 10 35 Q 25 50 50 40 Q 75 50 90 35 L 90 75 Q 75 90 50 80 Z" fill="#fdfbf7" stroke="#4a4542" strokeWidth="3" strokeLinejoin="round" />
        {/* Book Binding / Center line */}
        <line x1="50" y1="40" x2="50" y2="80" stroke="#4a4542" strokeWidth="2" strokeLinecap="round" />
        {/* Page Lines (Left) */}
        <line x1="20" y1="55" x2="40" y2="50" stroke="#ba493a" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        <line x1="20" y1="65" x2="40" y2="60" stroke="#ba493a" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        {/* Page Lines (Right) */}
        <line x1="80" y1="55" x2="60" y2="50" stroke="#ba493a" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        <line x1="80" y1="65" x2="60" y2="60" stroke="#ba493a" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        {/* Quill Feather */}
        <g className="quill-group">
          <path d="M 75 10 Q 85 20 70 35 Q 60 45 55 50 L 52 53 L 50 45 Q 60 25 75 10 Z" fill="#2a2725" />
          <path d="M 75 10 Q 80 20 70 35" fill="none" stroke="#fdfbf7" strokeWidth="1.5" />
        </g>
      </svg>
    </div>
  );
}

export default Mascot;
