import * as React from "react";

type IconProps = React.SVGProps<SVGSVGElement>;

export function OllamaIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <path
        d="M7.2 9.2c.5-3 2.3-5.2 4.8-5.2s4.3 2.2 4.8 5.2c1.6.9 2.7 2.5 2.7 4.4 0 3.4-3.3 6.1-7.5 6.1s-7.5-2.7-7.5-6.1c0-1.9 1.1-3.5 2.7-4.4Z"
        className="fill-current"
      />
      <path d="M9 12.1h.01M15 12.1h.01" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M10.6 15.1c.8.6 2 .6 2.8 0" stroke="white" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export function N8nIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <path d="M4 12h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="5" cy="12" r="2.5" className="fill-current" />
      <circle cx="12" cy="12" r="2.5" className="fill-current" />
      <circle cx="19" cy="12" r="2.5" className="fill-current" />
      <path d="M12 9.5V6m0 12v-3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function QdrantIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="12" cy="12" r="2.4" className="fill-current" />
      <path d="M12 4v5.4M12 14.6V20M4 12h5.4M14.6 12H20" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function PostgresqlIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <ellipse cx="12" cy="6.8" rx="6.5" ry="3.2" stroke="currentColor" strokeWidth="1.7" />
      <path d="M5.5 6.8v7.8c0 1.8 2.9 3.2 6.5 3.2s6.5-1.4 6.5-3.2V6.8" stroke="currentColor" strokeWidth="1.7" />
      <path d="M5.5 10.7c0 1.8 2.9 3.2 6.5 3.2s6.5-1.4 6.5-3.2" stroke="currentColor" strokeWidth="1.7" />
    </svg>
  );
}
