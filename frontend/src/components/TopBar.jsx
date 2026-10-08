import React from "react";
import { useProjects } from "../lib/store";
import { StatusBadge } from "../lib/ui";
import { GitBranch, FolderGit2, ChevronDown } from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator,
} from "./ui/dropdown-menu";

export default function TopBar() {
  const { projects, current, setCurrentId } = useProjects();

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-[#282E3A] bg-[#14171D]/95 px-4 pl-16 backdrop-blur lg:pl-4">
      <div className="flex min-w-0 items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              data-testid="topbar-project-switcher"
              className="flex min-w-0 items-center gap-2 rounded-md border border-[#282E3A] bg-[#1C2028] px-2.5 py-1.5 text-sm text-[#E2E8F0] hover:border-[#38BDF8]/40"
            >
              <FolderGit2 size={15} className="shrink-0 text-[#38BDF8]" />
              <span className="max-w-[140px] truncate font-medium sm:max-w-[220px]">
                {current ? current.name : "No project"}
              </span>
              <ChevronDown size={14} className="shrink-0 text-[#64748B]" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64 border-[#282E3A] bg-[#1C2028] text-[#E2E8F0]">
            <DropdownMenuLabel className="text-xs text-[#64748B]">Switch project</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-[#282E3A]" />
            {projects.map((p) => (
              <DropdownMenuItem
                key={p.id}
                data-testid={`switch-project-${p.id}`}
                onClick={() => setCurrentId(p.id)}
                className="flex items-center justify-between gap-2 focus:bg-[#282E3A]"
              >
                <span className="truncate">{p.name}</span>
                {current?.id === p.id && <span className="h-1.5 w-1.5 rounded-full bg-[#38BDF8]" />}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {current && (
          <>
            <span className="hidden font-mono text-xs text-[#64748B] md:inline truncate max-w-[220px]">
              {current.repo_url || "no-remote-configured"}
            </span>
            <div className="hidden items-center gap-1.5 rounded-md border border-[#282E3A] bg-[#0D0F12] px-2 py-1 font-mono text-xs text-[#94A3B8] sm:flex">
              <GitBranch size={13} className="text-[#38BDF8]" />
              {current.current_branch}
            </div>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        {current && <StatusBadge status={current.orchestration_status} testId="topbar-orchestration-status" />}
      </div>
    </header>
  );
}
