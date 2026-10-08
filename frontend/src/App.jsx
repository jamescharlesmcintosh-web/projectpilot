import React, {lazy,Suspense} from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { ProjectProvider } from "./lib/store";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

const Dashboard = lazy(()=>import("./pages/Dashboard"));
const Projects = lazy(()=>import("./pages/Projects"));
const ProjectOverview = lazy(()=>import("./pages/ProjectOverview"));
const MasterPlan = lazy(()=>import("./pages/MasterPlan"));
const DelegationPlan = lazy(()=>import("./pages/DelegationPlan"));
const TaskQueue = lazy(()=>import("./pages/TaskQueue"));
const TaskDetails = lazy(()=>import("./pages/TaskDetails"));
const LivePreview = lazy(()=>import("./pages/LivePreview"));
const Verification = lazy(()=>import("./pages/Verification"));
const GitDiffs = lazy(()=>import("./pages/GitDiffs"));
const Usage = lazy(()=>import("./pages/Usage"));
const ActivityLogs = lazy(()=>import("./pages/ActivityLogs"));
const Settings = lazy(()=>import("./pages/Settings"));

function Layout() {
  return (
    <div className="min-h-screen bg-[#0D0F12]">
      <Sidebar />
      <div className="lg:pl-64">
        <TopBar />
        <main className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6">
          <Suspense fallback={<p className="text-sm text-slate-400">Loading…</p>}><Outlet /></Suspense>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="App">
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/overview" element={<ProjectOverview />} />
              <Route path="/master-plan" element={<MasterPlan />} />
              <Route path="/delegation" element={<DelegationPlan />} />
              <Route path="/tasks" element={<TaskQueue />} />
              <Route path="/tasks/:taskId" element={<TaskDetails />} />
              <Route path="/preview" element={<LivePreview />} />
              <Route path="/verification" element={<Verification />} />
              <Route path="/git" element={<GitDiffs />} />
              <Route path="/usage" element={<Usage />} />
              <Route path="/activity" element={<ActivityLogs />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster theme="dark" position="bottom-right" richColors />
      </ProjectProvider>
    </div>
  );
}

export default App;
