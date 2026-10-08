// Lightweight LCS-based line diff for plan comparison.
export function diffLines(oldText, newText) {
  const a = (oldText || "").split("\n");
  const b = (newText || "").split("\n");
  const n = a.length;
  const m = b.length;
  // Bound memory for unusually large imported plans.
  if (n * m > 2000000) {
    let prefix=0; while(prefix<n && prefix<m && a[prefix]===b[prefix]) prefix++;
    let endA=n,endB=m; while(endA>prefix && endB>prefix && a[endA-1]===b[endB-1]){endA--;endB--;}
    return [...a.slice(0,prefix).map(line=>({type:"ctx",line})),...a.slice(prefix,endA).map(line=>({type:"del",line})),...b.slice(prefix,endB).map(line=>({type:"add",line})),...a.slice(endA).map(line=>({type:"ctx",line}))];
  }
  // LCS table
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const out = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ type: "ctx", line: a[i] });
      i++; j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ type: "del", line: a[i] });
      i++;
    } else {
      out.push({ type: "add", line: b[j] });
      j++;
    }
  }
  while (i < n) out.push({ type: "del", line: a[i++] });
  while (j < m) out.push({ type: "add", line: b[j++] });
  return out;
}

export function diffStats(rows) {
  const added = rows.filter((r) => r.type === "add").length;
  const removed = rows.filter((r) => r.type === "del").length;
  return { added, removed, changed: added + removed };
}

// Collapse long runs of unchanged context to keep the view focused.
export function collapseContext(rows, pad = 2) {
  const keep = new Array(rows.length).fill(false);
  rows.forEach((r, idx) => {
    if (r.type !== "ctx") {
      for (let k = Math.max(0, idx - pad); k <= Math.min(rows.length - 1, idx + pad); k++) keep[k] = true;
    }
  });
  const result = [];
  let skipped = 0;
  rows.forEach((r, idx) => {
    if (keep[idx]) {
      if (skipped > 0) {
        result.push({ type: "gap", line: `⋯ ${skipped} unchanged line${skipped > 1 ? "s" : ""}` });
        skipped = 0;
      }
      result.push(r);
    } else {
      skipped++;
    }
  });
  if (skipped > 0) result.push({ type: "gap", line: `⋯ ${skipped} unchanged line${skipped > 1 ? "s" : ""}` });
  return result;
}
