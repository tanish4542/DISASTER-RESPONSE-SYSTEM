export default function NetworkGraph() {
  return (
    <svg className="network-graph" viewBox="0 0 560 320" role="img" aria-label="Nearby devices relaying an SOS toward rescue operations">
      <line className="network-link" x1="90" y1="160" x2="210" y2="92" />
      <line className="network-link delay-1" x1="90" y1="160" x2="230" y2="220" />
      <line className="network-link delay-2" x1="210" y1="92" x2="340" y2="150" />
      <line className="network-link delay-3" x1="230" y1="220" x2="340" y2="150" />
      <line className="network-link delay-4" x1="340" y1="150" x2="470" y2="150" />

      <circle className="network-pulse" cx="90" cy="160" r="28" />
      <circle className="network-node victim" cx="90" cy="160" r="12" />
      <text x="90" y="196" textAnchor="middle">Victim</text>

      <circle className="network-pulse delay-1" cx="210" cy="92" r="22" />
      <circle className="network-node relay" cx="210" cy="92" r="9" />
      <text x="210" y="122" textAnchor="middle">Relay</text>

      <circle className="network-pulse delay-2" cx="230" cy="220" r="22" />
      <circle className="network-node relay" cx="230" cy="220" r="9" />
      <text x="230" y="250" textAnchor="middle">Relay</text>

      <circle className="network-pulse delay-3" cx="340" cy="150" r="24" />
      <circle className="network-node server" cx="340" cy="150" r="10" />
      <text x="340" y="186" textAnchor="middle">Backend</text>

      <circle className="network-pulse delay-4" cx="470" cy="150" r="26" />
      <circle className="network-node ops" cx="470" cy="150" r="11" />
      <text x="470" y="186" textAnchor="middle">Operations</text>
    </svg>
  );
}
