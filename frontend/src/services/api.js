const BASE_URL = 'http://127.0.0.1:8000/api';

const DEFAULT_FALLBACK_TOPOLOGY = {
  nodes: [
    { id: "User 041", label: "User 041", type: "user", color: "#3b82f6", val: 18, has_alert: true, is_selected: false, role: "Accused Suspect" },
    { id: "ACC-7741", label: "ACC-7741", type: "account", color: "#0284c7", val: 22, has_alert: true, is_selected: false, role: "Mule Account" },
    { id: "185.221.14.8", label: "185.221.14.8", type: "transaction", color: "#ef4444", val: 22, has_alert: true, is_selected: false, role: "IP Proxy" },
    { id: "DEV-992A", label: "DEV-992A", type: "device", color: "#f97316", val: 22, has_alert: true, is_selected: false, role: "Gateway Device" },
    { id: "ACC-1028", label: "ACC-1028", type: "account", color: "#0284c7", val: 26, has_alert: true, is_selected: false, role: "Aggregator Account" },
    { id: "User 882", label: "User 882", type: "user", color: "#3b82f6", val: 18, has_alert: true, is_selected: false, role: "Co-Conspirator" },
    { id: "TXN-8831", label: "TXN-8831", type: "transaction", color: "#ef4444", val: 24, has_alert: true, is_selected: false, role: "Exposure Txn" },
    { id: "ACC-5520", label: "ACC-5520", type: "account", color: "#0284c7", val: 22, has_alert: true, is_selected: false, role: "Transit Ledger" },
    { id: "10.42.8.64", label: "10.42.8.64", type: "device", color: "#f97316", val: 22, has_alert: true, is_selected: false, role: "Vishing IP Hop" },
    { id: "DEV-174Q", label: "DEV-174Q", type: "device", color: "#f97316", val: 28, has_alert: true, is_selected: true, role: "Mastermind Device" },
    { id: "TXN-8924", label: "TXN-8924", type: "transaction", color: "#ef4444", val: 24, has_alert: true, is_selected: false, role: "Velocity Txn" },
    { id: "ACC-7015", label: "ACC-7015", type: "account", color: "#0284c7", val: 22, has_alert: true, is_selected: false, role: "Cashout Account" }
  ],
  links: [
    { source: "User 041", target: "ACC-7741", relation: "", color: "#475569", dashed: false, dotted: true, weight: 1.2 },
    { source: "User 882", target: "ACC-1028", relation: "", color: "#475569", dashed: false, dotted: true, weight: 1.2 },
    { source: "ACC-7741", target: "185.221.14.8", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-7741", target: "ACC-1028", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "185.221.14.8", target: "DEV-992A", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "185.221.14.8", target: "ACC-1028", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "DEV-992A", target: "ACC-1028", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "DEV-992A", target: "TXN-8831", relation: "", color: "#475569", dashed: false, dotted: true, weight: 1.2 },
    { source: "ACC-1028", target: "TXN-8831", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "TXN-8831", target: "ACC-5520", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-5520", target: "10.42.8.64", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-5520", target: "TXN-8924", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "DEV-174Q", target: "10.42.8.64", relation: "device trail", color: "#eab308", dashed: true, dotted: false, weight: 2.0 },
    { source: "DEV-174Q", target: "TXN-8924", relation: "velocity sig", color: "#eab308", dashed: true, dotted: false, weight: 2.0 },
    { source: "DEV-174Q", target: "ACC-7015", relation: "shared device", color: "#eab308", dashed: false, dotted: false, weight: 2.5 },
    { source: "TXN-8924", target: "ACC-7015", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 }
  ]
};

export const fetchGraphTopology = async (samples = null) => {
  try {
    const url = samples ? `${BASE_URL}/graph-topology?samples=${samples}` : `${BASE_URL}/graph-topology`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    return data.data || DEFAULT_FALLBACK_TOPOLOGY;
  } catch (err) {
    console.warn('API Error fetching graph topology (using baseline fallback):', err);
    return DEFAULT_FALLBACK_TOPOLOGY;
  }
};

export const fetchSuspectConnections = async (personId) => {
  try {
    const res = await fetch(`${BASE_URL}/connections/${personId}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    return data.data;
  } catch (err) {
    console.error('API Error fetching suspect connections:', err);
    return null;
  }
};

export const extractFIRText = async (text) => {
  try {
    const res = await fetch(`${BASE_URL}/extract-fir`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    return data.data;
  } catch (err) {
    console.error('API Error extracting FIR text:', err);
    return null;
  }
};

export const analyzeDocumentFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/analyze-file`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed with status ${res.status}`);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error('File Analysis Error:', err);
    return null;
  }
};