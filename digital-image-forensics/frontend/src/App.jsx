
import { useState } from "react";
import "./styles.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const API = "http://127.0.0.1:8000";

  function handleFile(event) {
    setFile(event.target.files[0]);
    setResult(null);
    setError("");
  }

  async function analyzeImage() {
    if (!file) {
      setError("Please select an image.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the server.");
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
        throw new Error(data.detail || "Report generation failed.");
      }

      if (data.download_url) {
        const url = data.download_url.startsWith("http")
          ? data.download_url
          : `${API}${data.download_url}`;

        window.open(url, "_blank");
      } else {
        setError("Report link was not returned.");
      }
    } catch (err) {
      setError(err.message || "Could not generate report.");
    }
  }

  function value(item) {
    return item === undefined || item === null || item === ""
      ? "Not available"
      : String(item);
  }

  return (
    <div className="container">
      <header>
        <h1>Digital Image Forensics Tool</h1>
        <p>Image analysis and forgery detection</p>
      </header>

      <nav>
        <a href="#home">Home</a>
        <a href="#results">Results</a>
        <a href="#about">About</a>
      </nav>

      <section className="box" id="home">
        <h2>Upload Image</h2>
        <p>Select an image to analyze.</p>

        <input
          type="file"
          accept="image/*"
          onChange={handleFile}
        />

        {file && <p>Selected file: {file.name}</p>}

        <button onClick={analyzeImage} disabled={loading}>
          {loading ? "Please wait..." : "Analyze Image"}
        </button>

        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <div id="results">
          <section className="box">
            <h2>Analysis Result</h2>

            <table>
              <tbody>
                <tr>
                  <td>File Name</td>
                  <td>{value(result.filename)}</td>
                </tr>
                <tr>
                  <td>Case ID</td>
                  <td>{value(result.case_id)}</td>
                </tr>
                <tr>
                  <td>Forensic Score</td>
                  <td>{value(result.forensic_score)}</td>
                </tr>
                <tr>
                  <td>Risk Level</td>
                  <td>{value(result.risk)}</td>
                </tr>
                <tr>
                  <td>Analysis Time</td>
                  <td>{value(result.analysis_time)}</td>
                </tr>
                <tr>
                  <td>Conclusion</td>
                  <td>{value(result.conclusion)}</td>
                </tr>
              </tbody>
            </table>

            <p>
              Note: Results show possible signs of manipulation.
              They do not prove that an image is fake.
            </p>
          </section>

          <section className="box">
            <h2>Metadata</h2>
            <p>
              Software Detected:{" "}
              {value(result.metadata?.software_detected)}
            </p>
          </section>

          <section className="box">
            <h2>Error Level Analysis (ELA)</h2>
            <p>ELA Score: {value(result.ela?.score)}</p>

            {result.ela?.image_url && (
              <img
                className="analysis-image"
                src={`${API}${result.ela.image_url}`}
                alt="ELA analysis"
              />
            )}
          </section>

          <section className="box">
            <h2>Copy-Move Detection</h2>
            <p>Matches: {value(result.copy_move?.matches)}</p>
            <p>{value(result.copy_move?.message)}</p>

            {result.copy_move_image_url && (
              <img
                className="analysis-image"
                src={`${API}${result.copy_move_image_url}`}
                alt="Copy move analysis"
              />
            )}
          </section>

          <section className="box">
            <h2>Noise Analysis</h2>
            <p>
              Suspicious Blocks:{" "}
              {value(result.noise?.suspicious_blocks)}
            </p>
            <p>{value(result.noise?.message)}</p>

            {result.noise_image_url && (
              <img
                className="analysis-image"
                src={`${API}${result.noise_image_url}`}
                alt="Noise analysis"
              />
            )}
          </section>

          <section className="box">
            <h2>Image Hashes</h2>
            <p>MD5:</p>
            <p className="hash">{value(result.hashes?.md5)}</p>
            <p>SHA-256:</p>
            <p className="hash">{value(result.hashes?.sha256)}</p>
          </section>

          <button onClick={downloadReport}>
            Download PDF Report
          </button>
        </div>
      )}

      <section className="box" id="about">
        <h2>About the Project</h2>
        <p>
          This project checks images using metadata, ELA,
          copy-move detection, noise analysis and hashing.
          It helps identify possible signs of image editing.
        </p>
      </section>

      <footer>
        Digital Image Forensics Tool | College Project
      </footer>
    </div>
  );
}

export default App;
