import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getGuide, uploadGuide, lockGuide, updateGuide } from "../api/client";
import type { ResearchGuide, GuideReviewResult, AiFlag } from "../types/models";

export default function GuideReview() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [guide, setGuide] = useState<ResearchGuide | null>(null);
  const [reviewResult, setReviewResult] = useState<GuideReviewResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [locking, setLocking] = useState(false);

  // Upload form state
  const [objective, setObjective] = useState("");
  const [goals, setGoals] = useState("");

  useEffect(() => {
    if (!projectId) return;
    getGuide(projectId).then((d) => setGuide(d as ResearchGuide | null));
  }, [projectId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !projectId) return;
    setUploading(true);
    try {
      const result = (await uploadGuide(
        projectId,
        file,
        objective,
        goals
      )) as GuideReviewResult;
      setReviewResult(result);
      setGuide(result.parsed_guide);
    } catch (err) {
      alert(`Upload failed: ${err}`);
    } finally {
      setUploading(false);
    }
  };

  const handleLock = async () => {
    if (!projectId) return;
    setLocking(true);
    try {
      const locked = (await lockGuide(projectId)) as ResearchGuide;
      setGuide(locked);
    } finally {
      setLocking(false);
    }
  };

  const handleDismissFlag = async (flagIndex: number) => {
    if (!guide || !projectId) return;
    const updatedFlags = guide.review_flags.map((f: AiFlag, i: number) =>
      i === flagIndex ? { ...f, status: "dismissed" } : f
    );
    const updatedGuide = { ...guide, review_flags: updatedFlags };
    setGuide(updatedGuide as ResearchGuide);
    await updateGuide(projectId, updatedGuide);
  };

  // No guide yet — show upload form
  if (!guide) {
    return (
      <div className="page">
        <button onClick={() => navigate(-1)} className="back-link">&larr; Back</button>
        <h1>Upload Research Guide</h1>

        <div className="form-group">
          <label>Research Objective</label>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="What is this research trying to answer?"
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Research Goals (comma-separated)</label>
          <input
            type="text"
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            placeholder="Goal 1, Goal 2, Goal 3"
          />
        </div>

        <div className="form-group">
          <label>Guide File (Markdown)</label>
          <input
            type="file"
            accept=".md,.txt,.markdown"
            onChange={handleUpload}
            disabled={uploading}
          />
        </div>

        {uploading && <p className="muted">Uploading and analysing guide...</p>}
      </div>
    );
  }

  // Guide exists — show review view
  return (
    <div className="page">
      <button onClick={() => navigate(`/projects/${projectId}`)} className="back-link">
        &larr; Back to project
      </button>
      <h1>
        Research Guide
        {guide.locked && <span className="badge-locked"> Locked</span>}
      </h1>

      {guide.objective && (
        <div className="meta-block">
          <strong>Objective:</strong> {guide.objective}
        </div>
      )}
      {guide.research_goals.length > 0 && (
        <div className="meta-block">
          <strong>Goals:</strong> {guide.research_goals.join(", ")}
        </div>
      )}

      {/* AI Flags */}
      {guide.review_flags?.filter((f: AiFlag) => f.status !== "dismissed").length > 0 && (
        <div className="flags-panel">
          <h3>
            AI Review Flags (
            {guide.review_flags.filter((f: AiFlag) => f.status !== "dismissed").length}
            )
          </h3>
          {guide.review_flags.map((flag: AiFlag, i: number) =>
            flag.status === "dismissed" ? null : (
              <div key={i} className={`flag flag-${flag.flag_type}`}>
                <span className="flag-type">{flag.flag_type.replace(/_/g, " ")}</span>
                <p>{flag.message}</p>
                {flag.suggestion && (
                  <p className="flag-suggestion">Suggestion: {flag.suggestion}</p>
                )}
                <button onClick={() => handleDismissFlag(i)} className="btn-sm">
                  Dismiss
                </button>
              </div>
            )
          )}
        </div>
      )}

      {/* Coverage gaps */}
      {guide.coverage_gaps?.length > 0 && (
        <div className="flags-panel">
          <h3>Coverage Gaps</h3>
          {guide.coverage_gaps.map((gap: string, i: number) => (
            <p key={i} className="coverage-gap">No questions cover: {gap}</p>
          ))}
        </div>
      )}

      {guide.estimated_duration_minutes && (
        <p className="muted">
          Estimated duration: ~{guide.estimated_duration_minutes} minutes
        </p>
      )}

      {/* Guide sections */}
      <div className="guide-sections">
        {guide.sections.map((section) => (
          <div key={section.section_id} className="section-card">
            <h3>
              {section.section_name}
              {section.time_bracket && (
                <span className="time-bracket"> ({section.time_bracket})</span>
              )}
            </h3>
            <div className="question-list">
              {section.questions.map((q) => (
                <div key={q.question_id} className="question-item">
                  <div className="question-header">
                    <span className="question-id">{q.question_id}</span>
                    <span className="question-text">{q.question_text}</span>
                    {q.required && <span className="badge-required">Required</span>}
                  </div>
                  {q.mapped_goal && (
                    <p className="question-meta">Goal: {q.mapped_goal}</p>
                  )}
                  {q.probes.length > 0 && (
                    <div className="probes">
                      <span className="probes-label">Probes:</span>
                      {q.probes.map((probe, pi) => (
                        <span key={pi} className="probe">{probe}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {!guide.locked && (
        <div className="action-bar">
          <button onClick={handleLock} disabled={locking} className="btn btn-primary">
            {locking ? "Locking..." : "Lock Guide"}
          </button>
          <p className="muted">
            Locking commits this guide as the analysis framework for all transcripts.
          </p>
        </div>
      )}
    </div>
  );
}
