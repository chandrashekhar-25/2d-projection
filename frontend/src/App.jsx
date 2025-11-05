import React, { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [interval, setIntervalVal] = useState(1.0);
  const [maxFrames, setMaxFrames] = useState(10);
  const [status, setStatus] = useState("idle");
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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <div className="max-w-3xl w-full bg-white rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          🎥 2D Projection — Upload a Video
        </h1>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 border border-gray-200 rounded-xl p-6"
        >
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video File
            </label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {file && (
              <p className="text-sm text-gray-500 mt-2">{file.name}</p>
            )}
          </div>

          {/* Interval + Max Frames */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Interval (seconds)
              </label>
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={interval}
                onChange={(e) =>
                  setIntervalVal(parseFloat(e.target.value) || 1)
                }
                className="w-full rounded-lg border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Frames
              </label>
              <input
                type="number"
                min="1"
                value={maxFrames}
                onChange={(e) =>
                  setMaxFrames(parseInt(e.target.value) || 1)
                }
                className="w-full rounded-lg border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-medium hover:bg-indigo-700 transition-all duration-200 shadow-md"
            >
              Upload & Process
            </button>
          </div>
        </form>

        {/* Status */}
        <div className="mt-6 text-center text-sm text-gray-700">
          {status !== "idle" && (
            <div
              className={`inline-block px-4 py-2 rounded-lg ${
                status.startsWith("Error")
                  ? "bg-red-100 text-red-700"
                  : "bg-green-100 text-green-700"
              }`}
            >
              {status}
            </div>
          )}
        </div>

        {/* Results */}
        {frames.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Extracted Frames
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {frames.map((f) => (
                <div
                  key={f.filename}
                  className="rounded-lg overflow-hidden shadow hover:shadow-lg transition-shadow border border-gray-200"
                >
                  <img
                    src={f.data}
                    alt={f.filename}
                    className="w-full h-40 object-cover"
                  />
                  <div className="p-3 text-sm">
                    <strong className="block text-gray-800">
                      {f.filename}
                    </strong>
                    <p className="text-gray-600">
                      label: {f.label.label} (conf={f.label.confidence})
                    </p>
                    <p className="text-gray-600">
                      brightness: {f.label.brightness}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
