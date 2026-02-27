import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { listAllThemes, updateThemeStatus } from "../api/client";
import type { SessionThemes, Theme } from "../types/models";

export default function ThemesOverview() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [allThemes, setAllThemes] = useState<SessionThemes[]>([]);

  useEffect(() => {
    if (!projectId) return;
    listAllThemes(projectId).then((d) => setAllThemes(d as SessionThemes[]));
  }, [projectId]);

  const handleStatusChange = async (
    sessionId: string,
    themeId: string,
    status: string
  ) => {
    if (!projectId) return;
    await updateThemeStatus(projectId, sessionId, themeId, status);
    // Refresh
    const updated = (await listAllThemes(projectId)) as SessionThemes[];
    setAllThemes(updated);
  };

  return (
    <div className="page">
      <button
        onClick={() => navigate(`/projects/${projectId}`)}
        className="back-link"
      >
        &larr; Back to project
      </button>
      <h1>All Themes</h1>

      {allThemes.length === 0 ? (
        <p className="muted">No themes extracted yet.</p>
      ) : (
        allThemes.map((st) => (
          <div key={st.session_id} className="session-themes-group">
            <h2>
              {st.participant_id} &middot; {st.themes.length} themes
            </h2>
            {st.themes.map((theme: Theme) => (
              <div
                key={theme.theme_id}
                className={`theme-card theme-${theme.status}`}
              >
                <div className="theme-header">
                  <h4>{theme.theme_name}</h4>
                  <span className={`status-badge status-${theme.status}`}>
                    {theme.status}
                  </span>
                </div>
                <p>{theme.theme_description}</p>

                <div className="evidence-list">
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

                <div className="theme-actions">
                  <span className="muted">
                    {theme.instance_count} instances
                  </span>
                  {theme.status === "proposed" && (
                    <>
                      <button
                        onClick={() =>
                          handleStatusChange(
                            st.session_id,
                            theme.theme_id,
                            "accepted"
                          )
                        }
                        className="btn-sm btn-accept"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() =>
                          handleStatusChange(
                            st.session_id,
                            theme.theme_id,
                            "discarded"
                          )
                        }
                        className="btn-sm btn-discard"
                      >
                        Discard
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
