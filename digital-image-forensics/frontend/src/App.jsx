
import { useState } from "react";
import "./styles.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("ela");
  const [error, setError] = useState("");

  function handleFile(event) {
    const selected = event.target.files[0];

    if (!selected) return;

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError("");
  }

  async function analyzeImage() {
    if (!file) {
      setError("Please select an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Backend connection failed.");
    }

    setLoading(false);
  }

  async function downloadReport() {
    if (!result) return;

    try {
      const response = await fetch(
        `${API}/api/report/${result.analysis_id}`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Report generation failed");
      }

      if (data.download_url) {
        const url = data.download_url.startsWith("http")
          ? data.download_url
          : `${API}${data.download_url}`;

        window.open(url, "_blank");
      } else {
        setError("Report link not found.");
      }
    } catch (err) {
      setError(err.message);
    }
  }

  function getValue(value) {
    return value === null || value === undefined || value === ""
      ? "Not available"
      : value;
  }

  function getImage() {
    if (!result) return "";

    if (activeTab === "ela") {
      return result.ela?.image_url;
    }

    if (activeTab === "noise") {
      return result.noise_image_url;
    }

    if (activeTab === "copy") {
      return result.copy_move_image_url;
    }

    return "";
  }

  function getScore() {
    const score = Number(result?.forensic_score);
    return Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
  }

  function getRisk() {
    return String(result?.risk || "Not available");
  }

  return (
    <div className="app">

      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">⌕</span>
          <h2>PixelProbe</h2>
        </div>

        <nav>
          <a className="active" href="#analyze">Analyze</a>
          <a href="#metadata">Case files</a>
          <a href="#report">Reports</a>
          <a href="#about">Settings</a>
        </nav>

        <div className="case-number">
          {result ? `Case #${getValue(result.case_id)}` : "Image Forensics"}
        </div>
      </header>

      <main className="dashboard">

        {/* LEFT SIDE */}

        <aside className="left-column">

          <section className="panel upload-panel" id="analyze">
            <h3>Input image</h3>

            <label className="upload-area">
              <span className="upload-symbol">↑</span>
              <strong>Drop a file here</strong>
              <span>or</span>
              <span className="browse-button">Browse files</span>
              <small>JPEG, PNG, TIFF up to 25 MB</small>

              <input
                type="file"
                accept="image/*"
                onChange={handleFile}
              />
            </label>

            {file && (
              <div className="selected-file">
                <img src={preview} alt="Selected image" />
                <div>
                  <strong>{file.name}</strong>
                  <small>{(file.size / 1024 / 1024).toFixed(2)} MB</small>
                </div>
              </div>
            )}
          </section>

          <section className="panel methods-panel">
            <h3>Methods</h3>

            <div className="method">
              <span>✓</span> Error level analysis
            </div>

            <div className="method">
              <span>✓</span> EXIF / Metadata
            </div>

            <div className="method">
              <span>✓</span> Noise analysis
            </div>

            <div className="method">
              <span>✓</span> Copy-move detection
            </div>

            <button
              className="analyze-button"
              onClick={analyzeImage}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Run analysis"}
            </button>

            {error && <p className="error">{error}</p>}
          </section>

        </aside>

        {/* CENTER SIDE */}

        <section className="center-column">

          <section className="panel image-panel">
            <div className="tab-row">
              <button
                className={activeTab === "ela" ? "tab selected" : "tab"}
                onClick={() => setActiveTab("ela")}
              >
                Original vs ELA
              </button>

              <button
                className={activeTab === "noise" ? "tab selected" : "tab"}
                onClick={() => setActiveTab("noise")}
              >
                Noise
              </button>

              <button
                className={activeTab === "copy" ? "tab selected" : "tab"}
                onClick={() => setActiveTab("copy")}
              >
                Copy-move
              </button>
            </div>

            <div className="image-comparison">
              <div>
                {preview ? (
                  <img src={preview} alt="Original image" />
                ) : (
                  <div className="empty-image">Original image</div>
                )}
                <p>Original</p>
              </div>

              <div>
                {getImage() ? (
                  <img
                    src={`${API}${getImage()}`}
                    alt="Analysis result"
                  />
                ) : (
                  <div className="empty-image">
                    {result ? "No result image available" : "Analysis result"}
                  </div>
                )}
                <p>
                  {activeTab === "ela"
                    ? "ELA Result"
                    : activeTab === "noise"
                    ? "Noise Result"
                    : "Copy-move Result"}
                </p>
              </div>
            </div>
          </section>

          <section className="panel metadata-panel" id="metadata">
            <h3>Metadata</h3>

            <table>
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>File name</td>
                  <td>{getValue(result?.filename)}</td>
                  <td>-</td>
                </tr>

                <tr>
                  <td>Software</td>
                  <td>
                    {getValue(result?.metadata?.software_detected)}
                  </td>
                  <td>
                    {result?.metadata?.software_detected
                      ? "Detected"
                      : "Unknown"}
                  </td>
                </tr>

                <tr>
                  <td>ELA Score</td>
                  <td>{getValue(result?.ela?.score)}</td>
                  <td>-</td>
                </tr>

                <tr>
                  <td>Copy-move matches</td>
                  <td>{getValue(result?.copy_move?.matches)}</td>
                  <td>-</td>
                </tr>

                <tr>
                  <td>Suspicious noise blocks</td>
                  <td>
                    {getValue(result?.noise?.suspicious_blocks)}
                  </td>
                  <td>-</td>
                </tr>
              </tbody>
            </table>
          </section>

          {result && (
            <section className="panel hashes-panel">
              <h3>Image Hashes</h3>
              <p><strong>MD5:</strong> {getValue(result.hashes?.md5)}</p>
              <p><strong>SHA-256:</strong> {getValue(result.hashes?.sha256)}</p>
            </section>
          )}

        </section>

        {/* RIGHT SIDE */}

        <aside className="right-column">

          <section className="panel result-panel">
            <h3>Result</h3>

            <div
              className="score-circle"
              style={{
                "--score": `${getScore()}%`
              }}
            >
              <div>
                <strong>{result ? `${getScore()}%` : "--"}</strong>
                <small>Manipulation score</small>
              </div>
            </div>

            <div className="risk-label">
              {result ? getRisk() : "Waiting for analysis"}
            </div>

            <p className="conclusion">
              {result
                ? getValue(result.conclusion)
                : "Upload an image and run the analysis to see the result here."}
            </p>
          </section>

          <section className="panel findings-panel">
            <h3>Findings</h3>

            <div className="finding">
              <span>ELA analysis</span>
              <strong>{result ? getValue(result.ela?.score) : "-"}</strong>
            </div>

            <div className="finding">
              <span>Noise analysis</span>
              <strong>
                {result
                  ? getValue(result.noise?.suspicious_blocks)
                  : "-"}
              </strong>
            </div>

            <div className="finding">
              <span>Copy-move matches</span>
              <strong>
                {result
                  ? getValue(result.copy_move?.matches)
                  : "-"}
              </strong>
            </div>

            <div className="finding">
              <span>Software detected</span>
              <strong>
                {result
                  ? getValue(result.metadata?.software_detected)
                  : "-"}
              </strong>
            </div>
          </section>

          <section className="action-buttons" id="report">
            <button
              className="export-button"
              onClick={downloadReport}
              disabled={!result}
            >
              Export PDF
            </button>
          </section>

        </aside>

      </main>

      <footer id="about">
        Digital Image Forensics Tool | College Project
      </footer>

    </div>
  );
}

export default App;
