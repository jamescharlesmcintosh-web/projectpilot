import React from "react";
import { GitCompare, Plus, Minus } from "lucide-react";
import { diffStats, collapseContext } from "../lib/diff";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "./ui/dialog";

function Row({ row }) {
  if (row.type === "gap") {
    return <div className="select-none bg-[#111318] px-3 py-1 text-center font-mono text-[10px] text-[#475569]">{row.line}</div>;
  }
  const map = {
    add: { cls: "bg-emerald-950/30 text-[#4ADE80]", sign: "+" },
    del: { cls: "bg-rose-950/30 text-[#F87171]", sign: "-" },
    ctx: { cls: "text-[#64748B]", sign: " " },
  };
  const s = map[row.type];
  return (
    <div className={`flex gap-2 whitespace-pre-wrap px-3 ${s.cls}`}>
      <span className="select-none opacity-60">{s.sign}</span>
      <span className="flex-1 break-words">{row.line || " "}</span>
    </div>
  );
}

export default function PlanDiffDialog({ open, onOpenChange, title, rows }) {
  const stats = rows ? diffStats(rows) : { added: 0, removed: 0, changed: 0 };
  const view = rows ? collapseContext(rows) : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-hidden border-[#282E3A] bg-[#14171D] text-[#E2E8F0] sm:max-w-3xl" data-testid="plan-diff-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare size={17} className="text-[#38BDF8]" />
            {title}
          </DialogTitle>
          <DialogDescription className="text-[#64748B]">
            Line-by-line comparison between the previous plan and the freshly generated one.
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1 text-[#4ADE80]"><Plus size={12} />{stats.added} added</span>
          <span className="flex items-center gap-1 text-[#F87171]"><Minus size={12} />{stats.removed} removed</span>
        </div>
        {stats.changed === 0 ? (
          <div className="rounded-md border border-[#282E3A] bg-[#0D0F12] px-4 py-10 text-center text-sm text-[#64748B]" data-testid="plan-diff-empty">
            No changes — the regenerated plan is identical to the previous version.
          </div>
        ) : (
          <div className="max-h-[55vh] overflow-y-auto rounded-md border border-[#282E3A] bg-[#0D0F12] py-2 font-mono text-xs leading-relaxed pp-scroll-thin" data-testid="plan-diff-body">
            {view.map((r, i) => <Row key={i} row={r} />)}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
