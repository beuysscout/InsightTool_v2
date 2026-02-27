import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createProject, listProjects } from "../api/client";
import type { Project } from "../types/models";

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listProjects()
      .then((data) => setProjects(data as Project[]))
      .catch((err) => setError(`Failed to load projects: ${err.message}`))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const project = (await createProject(newName.trim())) as Project;
      setNewName("");
      navigate(`/projects/${project.project_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`Failed to create project: ${msg}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page">
      <h1>Projects</h1>

      {error && <p className="error-message">{error}</p>}

      <div className="create-form">
        <input
          type="text"
          placeholder="New project name..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          disabled={creating}
        />
        <button onClick={handleCreate} disabled={!newName.trim() || creating}>
          {creating ? "Creating..." : "Create Project"}
        </button>
      </div>

      {loading ? (
        <p className="muted">Loading...</p>
      ) : projects.length === 0 ? (
        <p className="muted">No projects yet. Create one to get started.</p>
      ) : (
        <div className="project-grid">
          {projects.map((p) => (
            <Link
              key={p.project_id}
              to={`/projects/${p.project_id}`}
              className="project-card"
            >
              <h3>{p.name}</h3>
              <div className="project-meta">
                <span className={`status-badge status-${p.status}`}>
                  {p.status.replace(/_/g, " ")}
                </span>
                <span>{p.session_count} sessions</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
