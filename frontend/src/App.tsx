import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProjectList from "./pages/ProjectList";
import ProjectDetail from "./pages/ProjectDetail";
import GuideReview from "./pages/GuideReview";
import TranscriptUpload from "./pages/TranscriptUpload";
import SessionDetail from "./pages/SessionDetail";
import ThemesOverview from "./pages/ThemesOverview";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="app-header">
          <a href="/" className="app-title">Insight Tool</a>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/projects/:projectId/guide" element={<GuideReview />} />
            <Route path="/projects/:projectId/upload" element={<TranscriptUpload />} />
            <Route path="/projects/:projectId/sessions/:sessionId" element={<SessionDetail />} />
            <Route path="/projects/:projectId/themes" element={<ThemesOverview />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
