import React, { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [interval, setIntervalVal] = useState(1.0);
  const [maxFrames, setMaxFrames] = useState(10);
  const [status, setStatus] = useState("");
  const [frames, setFrames] = useState([]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return alert("Select a video file");
    setStatus("Uploading...");
    setFrames([]);
    try {
      const fd = new FormData();
      fd.append("file", file, file.name);
      const params = new URLSearchParams({
        interval_seconds: String(interval),
        max_frames: String(maxFrames),
      });
      const res = await fetch(
        "http://localhost:8000/process-video?" + params.toString(),
        { method: "POST", body: fd }
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setFrames(data.frames || []);
      setStatus(`Received ${data.count} frames`);
    } catch (err) {
      console.error(err);
      setStatus("Error: " + (err.message || String(err)));
    }
  }

  return (
    <div className="container">
      <h1>2D Projection — Upload a Video</h1>
      <form onSubmit={handleSubmit} className="form">
        <label className="fileLabel">
          Video file
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <div className="controls">
          <label>
            Interval (s)
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={interval}
              onChange={(e) => setIntervalVal(parseFloat(e.target.value) || 1)}
            />
          </label>
          <label>
            Max frames
            <input
              type="number"
              min="1"
              value={maxFrames}
              onChange={(e) => setMaxFrames(parseInt(e.target.value) || 1)}
            />
          </label>
        </div>

        <div>
          <button type="submit">Upload & Process</button>
        </div>
      </form>

      <div className="status">{status}</div>

      {frames.length > 0 && (
        <>
          <h2>Result</h2>
          <div className="preview">
            {frames.map((f) => (
              <div className="card" key={f.filename}>
                <img src={f.data} alt={f.filename} />
                <div className="meta">
                  <strong>{f.filename}</strong>
                  <div>
                    <b>Detected objects:</b>
                    {f.label.objects.length
                      ? f.label.objects.map((obj, i) => (
                          <div key={i} style={{marginBottom: 4, marginLeft: 6}}>
                            type: {obj.type} <br />
                            bbox: [{obj.bbox.map(v => v.toFixed(1)).join(', ')}] <br />
                            confidence: {obj.confidence.toFixed(3)}
                          </div>
                        ))
                      : <span> None</span>
                    }
                  </div>
                  <div>
                    brightness: {f.label.meta.brightness}
                  </div>
                  <div>
                    mean color: [{f.label.meta.mean_color.join(', ')}]
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
