import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getSession,
  scanPii,
  anonymiseTranscript,
  organiseTranscript,
  extractThemes,
  getSessionThemes,
} from "../api/client";
import type {
  Session,
  PiiDetection,
  OrganisedTranscript,
  SessionThemes,
} from "../types/models";

export default function SessionDetail() {
  const { projectId, sessionId } = useParams<{
    projectId: string;
    sessionId: string;
  }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [piiDetections, setPiiDetections] = useState<PiiDetection[] | null>(null);
  const [themes, setThemes] = useState<SessionThemes | null>(null);
  const [processing, setProcessing] = useState("");
  const [interviewerName, setInterviewerName] = useState("");
  const [participantName, setParticipantName] = useState("");

  useEffect(() => {
    if (!projectId || !sessionId) return;
    getSession(projectId, sessionId).then((d) => {
      const s = d as Session;
      setSession(s);
      if (s.status === "themed") {
        getSessionThemes(projectId, sessionId).then((t) =>
          setThemes(t as SessionThemes)
        );
      }
    });
  }, [projectId, sessionId]);

  if (!session) return <p className="muted">Loading...</p>;

  const handleScanPii = async () => {
    if (!projectId || !sessionId) return;
    setProcessing("Scanning for personal information...");
    try {
      const dets = (await scanPii(
        projectId,
        sessionId,
        interviewerName || undefined,
        participantName || undefined
      )) as PiiDetection[];
      setPiiDetections(dets);
    } catch (err) {
      alert(`PII scan failed: ${err}`);
    }
    setProcessing("");
  };

  const handleToggleDetection = (index: number) => {
    if (!piiDetections) return;
    const updated = [...piiDetections];
    updated[index] = {
      ...updated[index],
      status: updated[index].status === "redacted" ? "kept" : "redacted",
    };
    setPiiDetections(updated);
  };

  const handleAnonymise = async () => {
    if (!projectId || !sessionId || !piiDetections) return;
    setProcessing("Applying redactions...");
    try {
      const s = (await anonymiseTranscript(
        projectId,
        sessionId,
        piiDetections
      )) as Session;
      setSession(s);
      setPiiDetections(null);
    } catch (err) {
      alert(`Anonymisation failed: ${err}`);
    }
    setProcessing("");
  };

  const handleOrganise = async () => {
    if (!projectId || !sessionId) return;
    setProcessing("AI is organising transcript against guide sections...");
    try {
      const organised = (await organiseTranscript(
        projectId,
        sessionId
      )) as OrganisedTranscript;
      setSession({ ...session, organised, status: "organised" });
    } catch (err) {
      alert(`Organisation failed: ${err}`);
    }
    setProcessing("");
  };

  const handleExtractThemes = async () => {
    if (!projectId || !sessionId) return;
    setProcessing("AI is extracting themes...");
    try {
      const t = (await extractThemes(projectId, sessionId)) as SessionThemes;
      setThemes(t);
      setSession({ ...session, status: "themed" });
    } catch (err) {
      alert(`Theme extraction failed: ${err}`);
    }
    setProcessing("");
  };

  return (
    <div className="page">
      <button
        onClick={() => navigate(`/projects/${projectId}`)}
        className="back-link"
      >
        &larr; Back to project
      </button>
      <h1>Session: {session.participant_id}</h1>
      <span className={`status-badge status-${session.status}`}>
        {session.status}
      </span>
      <span className="muted" style={{ marginLeft: 12 }}>
        {session.transcript.length} turns
      </span>

      {processing && <div className="processing-bar">{processing}</div>}

      {/* Step 2a: PII Scan */}
      {session.status === "uploaded" && !piiDetections && (
        <div className="action-bar">
          <div className="form-group" style={{ display: "flex", gap: 12, marginBottom: 12 }}>
            <div>
              <label>Interviewer name (optional)</label>
              <input
                type="text"
                value={interviewerName}
                onChange={(e) => setInterviewerName(e.target.value)}
                placeholder="e.g. Sarah"
              />
            </div>
            <div>
              <label>Participant name (optional)</label>
              <input
                type="text"
                value={participantName}
                onChange={(e) => setParticipantName(e.target.value)}
                placeholder="e.g. John"
              />
            </div>
          </div>
          <button onClick={handleScanPii} className="btn btn-primary">
            Scan for Personal Information
          </button>
        </div>
      )}

      {/* Step 2b: PII Review */}
      {piiDetections && (
        <div className="pii-review">
          <h3>Anonymisation Review</h3>
          <p className="muted">
            Found {piiDetections.length} items. Review each before
            anonymisation. Originals will be permanently discarded.
          </p>
          {piiDetections.length === 0 ? (
            <p>No personal information detected.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Original</th>
                  <th>Type</th>
                  <th>Replacement</th>
                  <th>Confidence</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {piiDetections.map((d, i) => (
                  <tr
                    key={i}
                    className={d.status === "kept" ? "row-kept" : ""}
                  >
                    <td>"{d.original_text}"</td>
                    <td>{d.pii_type}</td>
                    <td>{d.replacement_token}</td>
                    <td>{(d.confidence * 100).toFixed(0)}%</td>
                    <td>
                      <button
                        onClick={() => handleToggleDetection(i)}
                        className="btn-sm"
                      >
                        {d.status === "redacted" ? "Keep as-is" : "Redact"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="action-bar">
            <button onClick={handleAnonymise} className="btn btn-primary">
              Confirm &amp; Discard Original
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Organise */}
      {session.status === "anonymised" && (
        <div className="action-bar">
          <button onClick={handleOrganise} className="btn btn-primary">
            Organise Against Guide
          </button>
        </div>
      )}

      {/* Step 3 result: Organised table */}
      {session.organised && (
        <div className="organised-view">
          <h3>Organised Transcript</h3>
          <table className="data-table organised-table">
            <thead>
              <tr>
                <th>Guide Section</th>
                <th>Time Bracket</th>
                <th>Covered</th>
                <th>Participant Responses</th>
              </tr>
            </thead>
            <tbody>
              {session.organised.section_mappings.map((sm) => (
                <tr key={sm.section_id}>
                  <td className="section-name">{sm.section_name}</td>
                  <td className="time-bracket">{sm.time_bracket}</td>
                  <td>
                    <span
                      className={`coverage-badge coverage-${sm.coverage_status}`}
                    >
                      {sm.coverage_status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td>
                    {sm.mapped_turns.length === 0 ? (
                      <span className="muted">
                        {sm.coverage_notes || "No responses"}
                      </span>
                    ) : (
                      <div className="turn-list">
                        {sm.mapped_turns.map((mt) => (
                          <div key={mt.turn_index} className="mapped-turn">
                            <span className="turn-timestamp">
                              [{mt.timestamp}]
                            </span>{" "}
                            "{mt.text}"
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {session.organised.off_script_turns.length > 0 && (
            <div className="off-script">
              <h4>Off-script responses</h4>
              {session.organised.off_script_turns.map((t) => (
                <div key={t.turn_index} className="mapped-turn">
                  <span className="turn-timestamp">[{t.timestamp}]</span>{" "}
                  "{t.text}"
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 4: Extract themes */}
      {session.status === "organised" && !themes && (
        <div className="action-bar">
          <button onClick={handleExtractThemes} className="btn btn-primary">
            Extract Themes
          </button>
        </div>
      )}

      {/* Step 4 result: Themes */}
      {themes && (
        <div className="themes-view">
          <h3>Themes ({themes.themes.length})</h3>
          {themes.themes.map((theme) => (
            <div key={theme.theme_id} className="theme-card">
              <h4>{theme.theme_name}</h4>
              <p>{theme.theme_description}</p>
              <div className="evidence-list">
                <strong>Supporting evidence:</strong>
                {theme.evidence.map((ev, i) => (
                  <div key={i} className="evidence-item">
                    <span className="evidence-quote">"{ev.quote}"</span>
                    <span className="evidence-meta">
                      {" "}
                      &mdash; {ev.participant_id}, {ev.timestamp},{" "}
                      {ev.guide_section}
                    </span>
                  </div>
                ))}
              </div>
              <div className="theme-meta">
                Instances: {theme.instance_count} &middot; Status: {theme.status}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Raw transcript (collapsible) */}
      <details className="raw-transcript">
        <summary>Raw transcript ({session.transcript.length} turns)</summary>
        <div className="turn-list">
          {session.transcript.map((turn) => (
            <div
              key={turn.turn_index}
              className={`turn ${turn.is_interviewer ? "turn-interviewer" : "turn-participant"}`}
            >
              <span className="turn-timestamp">[{turn.timestamp}]</span>
              <span className="turn-speaker">
                {turn.is_interviewer ? "INTERVIEWER" : turn.speaker}:
              </span>
              <span className="turn-text"> {turn.text}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
