import React from "react";
import clsx from "clsx";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}
export function Card({ className, ...props }: CardProps) {
  return <div className={clsx("card", className)} {...props} />;
}

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "warning" | "danger" | "primary" | "default";
}
export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  return <span className={clsx("badge", variant !== "default" && variant, className)} {...props} />;
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
}
export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  return (
    <button className={clsx("btn", `btn-${variant}`, className)} {...props} />
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}
export function Input({ className, ...props }: InputProps) {
  return <input className={clsx("input-field", className)} {...props} />;
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {children && <div>{children}</div>}
    </div>
  );
}
