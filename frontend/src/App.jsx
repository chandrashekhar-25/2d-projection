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
                <img src={f.data} alt={f.filename} style={{width:'100%',maxWidth:350}} />
                <div className="meta">
                  <strong>{f.filename}</strong>
                  
                  <div>
                    <b>Detected objects:</b>
                    {f.label.objects.length ? (
                      <div style={{display:'flex',flexWrap:'wrap',gap:'10px',marginTop:'5px'}}>
                        {f.label.objects.map((obj, i) => (
                          <div key={i} className="object-card"
                               style={{
                                 border: '1px solid #ddd',
                                 borderRadius: '6px',
                                 padding: '8px',
                                 background: '#f9f9fa',
                                 minWidth: 140,
                                 boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
                               }}>
                            <div><b>{obj.type}</b></div>
                            <div>
                              <small>Box:</small> <span>[{obj.bbox.map(v => v.toFixed(1)).join(', ')}]</span>
                            </div>
                            <div>
                              <small>Confidence:</small> {obj.confidence?.toFixed(3)}
                            </div>
                            {obj.attributes && (
                              <div style={{marginTop:'5px'}}>
                                {Object.entries(obj.attributes).map(([k,v]) => (
                                  <span key={k} style={{marginRight:8}}>
                                    <small>{k}:</small> <span>{String(v)}</span>
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : <span> None</span>}
                  </div>
                  <div style={{marginTop:"5px"}}>
                    <b>Meta:</b>
                    <div>brightness: {f.label.meta.brightness}</div>
                    <div>mean color: [{f.label.meta.mean_color.join(', ')}]</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      {/* Add minimal CSS for demonstration */}
      <style>{"\
        .container { max-width:900px; margin:auto; font-family:sans-serif; padding:16px; }\
        .preview { display:flex; flex-wrap:wrap; gap:20px; margin-top:15px;}\
        .card { background:#fff; border:1px solid #dedede; border-radius:8px; \
          padding:14px;margin-bottom:15px; box-shadow:0 3px 16px rgba(0,0,0,0.08); width:380px;}\
        .meta { margin-top:10px; font-size:14px;}\
        .form { margin-bottom:24px; }\
        .controls { margin-bottom:14px; display:flex; gap:28px; }\
        .fileLabel { margin-right:10px; }\
        .status { margin:10px 0; color:#444; }\
        .object-card { margin-top:2px; }\
      "}</style>
    </div>
  );
}
