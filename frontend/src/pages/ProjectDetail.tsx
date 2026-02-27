import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProject, getGuide, listSessions } from "../api/client";
import type { Project, ResearchGuide, Session } from "../types/models";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [guide, setGuide] = useState<ResearchGuide | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    if (!projectId) return;
    getProject(projectId).then((d) => setProject(d as Project));
    getGuide(projectId).then((d) => setGuide(d as ResearchGuide | null));
    listSessions(projectId).then((d) => setSessions(d as Session[]));
  }, [projectId]);

  if (!project) return <p className="muted">Loading...</p>;

  return (
    <div className="page">
      <Link to="/" className="back-link">&larr; All projects</Link>
      <h1>{project.name}</h1>
      <span className={`status-badge status-${project.status}`}>
        {project.status.replace(/_/g, " ")}
      </span>

      {/* Step 1: Guide */}
      <section className="section-card">
        <h2>Research Guide</h2>
        {!guide ? (
          <div>
            <p className="muted">No guide uploaded yet.</p>
            <Link to={`/projects/${projectId}/guide`} className="btn">
              Upload Guide
            </Link>
          </div>
        ) : (
          <div>
            <p>
              {guide.sections.length} sections, {" "}
              {guide.sections.reduce((n, s) => n + s.questions.length, 0)} questions
              {guide.locked && <span className="badge-locked"> Locked</span>}
            </p>
            <Link to={`/projects/${projectId}/guide`} className="btn">
              {guide.locked ? "View Guide" : "Review Guide"}
            </Link>
          </div>
        )}
      </section>

      {/* Step 2+: Sessions */}
      <section className="section-card">
        <h2>Sessions</h2>
        {sessions.length === 0 ? (
          <p className="muted">No transcripts uploaded yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Participant</th>
                <th>Status</th>
                <th>Turns</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.session_id}>
                  <td>{s.participant_id}</td>
                  <td>
                    <span className={`status-badge status-${s.status}`}>
                      {s.status}
                    </span>
                  </td>
                  <td>{s.transcript.length}</td>
                  <td>
                    <Link to={`/projects/${projectId}/sessions/${s.session_id}`}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {guide?.locked && (
          <Link to={`/projects/${projectId}/upload`} className="btn" style={{ marginTop: 12 }}>
            Upload Transcript
          </Link>
        )}
      </section>

      {/* Themes overview */}
      {sessions.some((s) => s.status === "themed") && (
        <section className="section-card">
          <h2>Themes</h2>
          <Link to={`/projects/${projectId}/themes`} className="btn">
            View All Themes
          </Link>
        </section>
      )}
    </div>
  );
}
