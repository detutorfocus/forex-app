import React from "react";

type Props = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ label, className = "", ...props }: Props) {
  return (
    <label className="block space-y-1">
      <div className="text-sm text-slate-300">{label}</div>
      <input
        className={`w-full rounded-xl bg-slate-900 border border-slate-800 px-3 py-2 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500 ${className}`}
        {...props}
      />
    </label>
  );
}
