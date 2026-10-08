import React from "react";
import { Link } from "react-router-dom";
import { FolderGit2 } from "lucide-react";
import { EmptyState } from "./Primitives";
import { Button } from "./ui/button";

export default function NoProject({ label = "Select or create a project to continue." }) {
  return (
    <EmptyState
      testId="no-project-empty"
      icon={FolderGit2}
      title="No project selected"
      description={label}
      action={
        <Link to="/projects">
          <Button data-testid="goto-projects-btn" className="bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
            Go to Projects
          </Button>
        </Link>
      }
    />
  );
}
