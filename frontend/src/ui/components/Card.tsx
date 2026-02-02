import React from "react";

export function Card({ title, children, right }: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        {right}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}
