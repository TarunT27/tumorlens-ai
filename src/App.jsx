import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Brain,
  Check,
  ChevronRight,
  CircleDot,
  Download,
  Eye,
  FileJson,
  Layers3,
  LineChart,
  Play,
  RefreshCw,
  Server,
  SlidersHorizontal,
  Upload,
} from "lucide-react";

const steps = [
  { id: "load", label: "Load Scan", detail: "BraTS MRI volume" },
  { id: "connect", label: "Connect MONAI", detail: "Label server" },
  { id: "segment", label: "Run AI Segmentation", detail: "deepedit inference" },
  { id: "review", label: "Review 2D/3D", detail: "Slices and surface" },
  { id: "measure", label: "Inspect Measurements", detail: "Tumor analytics" },
  { id: "export", label: "Export Report", detail: "JSON or CSV" },
];

const metrics = [
  { label: "Tumor volume", value: "38.42", unit: "cm^3", trend: "+4.8% growth" },
  { label: "Voxel count", value: "184,920", unit: "voxels", trend: "T1CE mask" },
  { label: "Surface area", value: "4,812", unit: "mm^2", trend: "closed surface" },
  { label: "Bounding box", value: "48 x 37 x 29", unit: "mm", trend: "A/P - L/R - S/I" },
  { label: "Center of mass", value: "22.6, -14.2, 38.9", unit: "mm", trend: "RAS coordinates" },
  { label: "Margin distance", value: "6.4", unit: "mm", trend: "planning estimate" },
];

const labelRows = [
  { id: "enhancing", label: "Enhancing tumor", color: "#22d3ee", volume: "14.8 cm^3" },
  { id: "edema", label: "Peritumoral edema", color: "#60a5fa", volume: "19.6 cm^3" },
  { id: "necrotic", label: "Necrotic core", color: "#f472b6", volume: "4.0 cm^3" },
];

const surfaceCopy = {
  console: {
    title: "Guided workflow console",
    copy: "Walk through load, MONAI connection, segmentation, review, measurement, and report export from one clinical surface.",
  },
  slicer: {
    title: "3D Slicer module preview",
    copy: "The same control model maps to the scripted Slicer panel: volume node, MONAI endpoint, model, overlays, and exports.",
  },
  portfolio: {
    title: "Portfolio demo surface",
    copy: "Recruiter-friendly evidence: real workflow, imaging outputs, quantitative metrics, and non-clinical disclaimer in one view.",
  },
};

function App() {
  const [activeStep, setActiveStep] = useState("review");
  const [surface, setSurface] = useState("console");
  const [scanLoaded, setScanLoaded] = useState(true);
  const [connected, setConnected] = useState(true);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(100);
  const [opacity, setOpacity] = useState(68);
  const [showReport, setShowReport] = useState(false);
  const [labels, setLabels] = useState({
    enhancing: true,
    edema: true,
    necrotic: true,
  });

  useEffect(() => {
    if (!running) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 100) {
          window.clearInterval(timer);
          setRunning(false);
          setActiveStep("review");
          return 100;
        }
        return Math.min(current + 8, 100);
      });
    }, 260);

    return () => window.clearInterval(timer);
  }, [running]);

  const statusLabel = useMemo(() => {
    if (running) return `Segmenting ${progress}%`;
    if (!connected) return "MONAI offline";
    if (!scanLoaded) return "Awaiting scan";
    return "Ready for review";
  }, [connected, progress, running, scanLoaded]);

  function loadSampleScan() {
    setScanLoaded(true);
    setActiveStep("load");
  }

  function connectServer() {
    setConnected(true);
    setActiveStep("connect");
  }

  function runSegmentation() {
    if (!scanLoaded || !connected) return;
    setActiveStep("segment");
    setProgress(0);
    setRunning(true);
  }

  function exportReport(format) {
    setActiveStep("export");
    setShowReport(true);
    const payload = {
      studyId: "BraTS_2021_001",
      modality: "MRI T1CE",
      model: "deepedit / 3D UNet",
      tumorVolumeCm3: 38.42,
      voxelCount: 184920,
      surfaceAreaMm2: 4812,
      boundingBoxMm: [48, 37, 29],
      centerOfMassMm: [22.6, -14.2, 38.9],
      marginDistanceMm: 6.4,
      labels: labelRows.filter((row) => labels[row.id]).map((row) => row.label),
      disclaimer: "Research and education demo. Not for clinical diagnosis or treatment.",
    };
    const body =
      format === "csv"
        ? Object.entries(payload)
            .map(([key, value]) => `${key},${JSON.stringify(value)}`)
            .join("\n")
        : JSON.stringify(payload, null, 2);
    const blob = new Blob([body], { type: format === "csv" ? "text/csv" : "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `tumorlens-report.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-shell">
      <TopBar statusLabel={statusLabel} connected={connected} onExport={() => exportReport("json")} />

      <aside className="workflow-rail" aria-label="TumorLens AI workflow">
        <div className="brand-stack">
          <span className="brand-mark">
            <Brain size={21} />
          </span>
          <div>
            <strong>TumorLens AI</strong>
            <span>3D Slicer + MONAI</span>
          </div>
        </div>

        <div className="workflow-list">
          {steps.map((step, index) => {
            const selected = step.id === activeStep;
            const complete = steps.findIndex((item) => item.id === activeStep) > index || progress === 100;
            return (
              <button
                className={`workflow-step ${selected ? "is-active" : ""}`}
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                type="button"
              >
                <span className={`step-index ${complete ? "is-complete" : ""}`}>
                  {complete ? <Check size={14} /> : index + 1}
                </span>
                <span>
                  <strong>{step.label}</strong>
                  <small>{step.detail}</small>
                </span>
                <ChevronRight size={15} />
              </button>
            );
          })}
        </div>

        <div className="slicer-card">
          <div className="mini-title">
            <Layers3 size={15} />
            Slicer module
          </div>
          <p>Volume node, inference, closed surface, metrics, and export share the same logic API.</p>
        </div>
      </aside>

      <main className="workspace">
        <section className="surface-tabs" aria-label="Demo surface">
          {Object.entries(surfaceCopy).map(([id, item]) => (
            <button
              className={surface === id ? "selected" : ""}
              key={id}
              onClick={() => setSurface(id)}
              type="button"
            >
              {item.title}
            </button>
          ))}
        </section>

        <section className="hero-strip">
          <div>
            <h1>{surfaceCopy[surface].title}</h1>
            <p>{surfaceCopy[surface].copy}</p>
          </div>
          <div className="status-cluster">
            <span className={connected ? "status-pill online" : "status-pill"}>
              <CircleDot size={14} />
              {connected ? "MONAI connected" : "MONAI offline"}
            </span>
            <span className="status-pill">
              <Activity size={14} />
              MRI T1CE
            </span>
          </div>
        </section>

        <div className="content-grid">
          <ImagingWorkspace opacity={opacity} labels={labels} running={running} progress={progress} surface={surface} />

          <ContextPanel
            activeStep={activeStep}
            connected={connected}
            labels={labels}
            loadSampleScan={loadSampleScan}
            opacity={opacity}
            progress={progress}
            running={running}
            setConnected={setConnected}
            setLabels={setLabels}
            setOpacity={setOpacity}
            connectServer={connectServer}
            runSegmentation={runSegmentation}
            exportReport={exportReport}
          />
        </div>

        <MetricsBand metrics={metrics} labels={labels} showReport={showReport} setShowReport={setShowReport} />
      </main>
    </div>
  );
}

function TopBar({ connected, onExport, statusLabel }) {
  return (
    <header className="topbar">
      <div className="study-meta">
        <span className="eyeline">Active study</span>
        <strong>BraTS_2021_001</strong>
        <span>MRI T1CE - research demo</span>
      </div>

      <div className="server-meta">
        <span className={connected ? "dot online" : "dot"} />
        <span>{statusLabel}</span>
      </div>

      <div className="top-actions">
        <button className="ghost-button" type="button">
          <RefreshCw size={16} />
          Sync volume
        </button>
        <button className="primary-button" onClick={onExport} type="button">
          <Download size={16} />
          Export report
        </button>
      </div>
    </header>
  );
}

function ImagingWorkspace({ labels, opacity, progress, running, surface }) {
  return (
    <section className="image-console" aria-label="Medical imaging review workspace">
      <div className="image-console-header">
        <div>
          <span className="eyeline">Review canvas</span>
          <h2>2D slices and 3D tumor surface</h2>
        </div>
        <div className="viewport-tools">
          <span>Opacity {opacity}%</span>
          <span>{running ? `Inference ${progress}%` : "Closed surface ready"}</span>
        </div>
      </div>

      <div className={`viewer-layout viewer-${surface}`}>
        <div className="slice-stack">
          <MedicalPane title="Axial" image="/assets/tumorlens/mri-axial.png" active />
          <MedicalPane title="Sagittal" image="/assets/tumorlens/mri-sagittal.png" />
          <MedicalPane title="Coronal" image="/assets/tumorlens/mri-coronal.png" />
        </div>

        <div className="model-pane">
          <img alt="3D brain surface with AI tumor segmentation" src="/assets/tumorlens/model-3d.png" />
          <div className="model-overlay top">
            <span>3D closed surface</span>
            <strong>Segmentation visible</strong>
          </div>
          <div className="model-overlay bottom">
            {labelRows.map((row) => (
              <span className={labels[row.id] ? "" : "muted"} key={row.id}>
                <i style={{ backgroundColor: row.color }} />
                {row.label}
              </span>
            ))}
          </div>
          {running && (
            <div className="inference-scrim">
              <Activity size={28} />
              <strong>MONAI inference running</strong>
              <span>{progress}% complete</span>
            </div>
          )}
        </div>
      </div>

      <div className="console-footer" aria-label="Pipeline telemetry">
        <TelemetryItem label="Volume node" value="vtkMRMLScalarVolumeNode" />
        <TelemetryItem label="Inference response" value={running ? "MONAI Label processing" : "Labelmap imported"} />
        <TelemetryItem label="3D output" value="Closed surface model ready" />
      </div>
    </section>
  );
}

function TelemetryItem({ label, value }) {
  return (
    <div className="telemetry-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MedicalPane({ active = false, image, title }) {
  return (
    <article className={`medical-pane ${active ? "active" : ""}`}>
      <img alt={`${title} MRI slice with segmentation overlay`} src={image} />
      <div className="pane-chrome">
        <strong>{title}</strong>
        <span>slice 84 / 155</span>
      </div>
    </article>
  );
}

function ContextPanel({
  activeStep,
  connected,
  connectServer,
  exportReport,
  labels,
  loadSampleScan,
  opacity,
  progress,
  runSegmentation,
  running,
  setConnected,
  setLabels,
  setOpacity,
}) {
  return (
    <aside className="context-panel">
      <div className="panel-heading">
        <span className="eyeline">Current action</span>
        <h2>{steps.find((step) => step.id === activeStep)?.label}</h2>
      </div>

      <div className="control-group">
        <label>Volume</label>
        <button className="field-button" onClick={loadSampleScan} type="button">
          <Upload size={16} />
          BraTS_2021_001_T1CE.nii.gz
        </button>
      </div>

      <div className="control-group">
        <label>MONAI Label server</label>
        <div className="input-row">
          <Server size={16} />
          <input value="http://127.0.0.1:8000" readOnly />
        </div>
        <button className={connected ? "secondary-button success" : "secondary-button"} onClick={connectServer} type="button">
          {connected ? "Connected" : "Connect server"}
        </button>
      </div>

      <div className="control-grid">
        <div className="control-group">
          <label>Model</label>
          <select defaultValue="deepedit">
            <option value="deepedit">deepedit / 3D UNet</option>
            <option value="segresnet">SegResNet brain tumor</option>
          </select>
        </div>
        <div className="control-group">
          <label>Status</label>
          <div className="status-meter">
            <span style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      <button className="primary-button wide" disabled={running} onClick={runSegmentation} type="button">
        <Play size={16} />
        {running ? "Running inference" : "Run AI segmentation"}
      </button>

      <div className="control-group">
        <label>Segmentation opacity</label>
        <input max="100" min="0" onChange={(event) => setOpacity(event.target.value)} type="range" value={opacity} />
      </div>

      <div className="label-list">
        <div className="mini-title">
          <Eye size={15} />
          Label visibility
        </div>
        {labelRows.map((row) => (
          <label className="label-row" key={row.id}>
            <input
              checked={labels[row.id]}
              onChange={(event) => setLabels((current) => ({ ...current, [row.id]: event.target.checked }))}
              type="checkbox"
            />
            <span style={{ "--label-color": row.color }} />
            <strong>{row.label}</strong>
            <small>{row.volume}</small>
          </label>
        ))}
      </div>

      <div className="quality-list">
        <div className="mini-title">
          <SlidersHorizontal size={15} />
          Quality checks
        </div>
        <QualityRow label="Reference geometry" value="Aligned" />
        <QualityRow label="Closed surface" value="Generated" />
        <QualityRow label="Margin distance" value="6.4 mm" />
      </div>

      <div className="export-row">
        <button className="ghost-button" onClick={() => exportReport("json")} type="button">
          <FileJson size={15} />
          JSON
        </button>
        <button className="ghost-button" onClick={() => exportReport("csv")} type="button">
          <Download size={15} />
          CSV
        </button>
      </div>

      <button className="link-button" onClick={() => setConnected(false)} type="button">
        Simulate server disconnect
      </button>
    </aside>
  );
}

function QualityRow({ label, value }) {
  return (
    <div className="quality-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MetricsBand({ labels, metrics, setShowReport, showReport }) {
  return (
    <section className="metrics-band" aria-label="Quantitative tumor measurements and report preview">
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <article className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>
              {metric.value} <small>{metric.unit}</small>
            </strong>
            <em>{metric.trend}</em>
          </article>
        ))}
      </div>

      <aside className="report-preview">
        <div className="mini-title">
          <LineChart size={15} />
          Report preview
        </div>
        <div className="report-lines">
          <span>Organ involvement: adjacent edema, no ventricle crossing in demo mask</span>
          <span>Visible labels: {labelRows.filter((row) => labels[row.id]).length} / 3</span>
          <span>Readiness: segmentation, surface, and metrics complete</span>
        </div>
        <button className="secondary-button" onClick={() => setShowReport(!showReport)} type="button">
          {showReport ? "Hide report details" : "Open report details"}
        </button>
      </aside>

      {showReport && (
        <div className="report-drawer">
          <strong>Research demo disclaimer</strong>
          <p>
            TumorLens AI demonstrates medical imaging engineering workflows for education and portfolio review. It is not
            a medical device and does not provide diagnosis, treatment advice, or clinical decision support.
          </p>
        </div>
      )}
    </section>
  );
}

export default App;
