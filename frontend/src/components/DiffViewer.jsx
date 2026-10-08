import React from "react";
import { FileCode2, Plus, Minus } from "lucide-react";

function HunkLine({ line }) {
  let cls = "diff-meta";
  if (line.startsWith("+")) cls = "diff-add";
  else if (line.startsWith("-")) cls = "diff-del";
  else if (line.startsWith("@@")) cls = "diff-meta";
  return <div className={`whitespace-pre px-3 ${cls}`}>{line || " "}</div>;
}

export default function DiffViewer({ diff, testId }) {
  if (!diff) return null;
  return (
    <div data-testid={testId} className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
        <span className="font-mono text-[#94A3B8]">branch: <span className="text-[#38BDF8]">{diff.branch}</span></span>
        <span className="text-[#64748B]">{diff.summary}</span>
      </div>
      <div className="space-y-3">
        {diff.files.map((f, i) => (
          <div key={i} className="overflow-hidden rounded-md border border-[#282E3A] bg-[#0D0F12]">
            <div className="flex items-center justify-between border-b border-[#282E3A] bg-[#14171D] px-3 py-2">
              <div className="flex items-center gap-2 font-mono text-xs text-[#E2E8F0]">
                <FileCode2 size={13} className="text-[#64748B]" /> {f.path}
              </div>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="flex items-center gap-0.5 text-[#4ADE80]"><Plus size={11} />{f.additions}</span>
                <span className="flex items-center gap-0.5 text-[#F87171]"><Minus size={11} />{f.deletions}</span>
              </div>
            </div>
            <div className="overflow-x-auto py-2 font-mono text-xs leading-relaxed">
              {f.hunk.split("\n").map((line, j) => <HunkLine key={j} line={line} />)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
