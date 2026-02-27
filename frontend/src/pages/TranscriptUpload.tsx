import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { uploadTranscript } from "../api/client";
import type { Session } from "../types/models";

export default function TranscriptUpload() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<Session[]>([]);

  const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || !projectId) return;

    setUploading(true);
    const results: Session[] = [];
    for (const file of Array.from(files)) {
      try {
        const session = (await uploadTranscript(projectId, file)) as Session;
        results.push(session);
      } catch (err) {
        alert(`Failed to upload ${file.name}: ${err}`);
      }
    }
    setUploaded(results);
    setUploading(false);
  };

  return (
    <div className="page">
      <button onClick={() => navigate(`/projects/${projectId}`)} className="back-link">
        &larr; Back to project
      </button>
      <h1>Upload Transcripts</h1>

      <div className="upload-zone">
        <input
          type="file"
          accept=".md,.txt,.markdown"
          multiple
          onChange={handleFiles}
          disabled={uploading}
        />
        <p className="muted">
          Upload one or more markdown transcripts from Askable.
          Each file becomes a separate session.
        </p>
      </div>

      {uploading && <p className="muted">Uploading and parsing transcripts...</p>}

      {uploaded.length > 0 && (
        <div>
          <h3>Uploaded ({uploaded.length})</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Participant</th>
                <th>Turns</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {uploaded.map((s) => (
                <tr key={s.session_id}>
                  <td>{s.participant_id}</td>
                  <td>{s.transcript.length}</td>
                  <td>{s.status}</td>
                  <td>
                    <button
                      onClick={() =>
                        navigate(`/projects/${projectId}/sessions/${s.session_id}`)
                      }
                      className="btn-sm"
                    >
                      Review &amp; Anonymise
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
