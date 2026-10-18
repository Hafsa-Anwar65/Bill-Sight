import type { SVGProps } from "react";

const base = (d: React.ReactNode) => (p: SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...p}>
    {d}
  </svg>
);

export const Bolt = base(<path d="M13 2 4 14h7l-1 8 9-12h-7z" />);
export const Receipt = base(<><path d="M6 2h12v20l-3-2-3 2-3-2-3 2z" /><path d="M9 7h6M9 11h6M9 15h4" /></>);
export const Percent = base(<><path d="M19 5 5 19" /><circle cx="7" cy="7" r="2.5" /><circle cx="17" cy="17" r="2.5" /></>);
export const Calendar = base(<><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></>);
export const Trend = base(<><path d="m3 17 6-6 4 4 8-8" /><path d="M15 7h6v6" /></>);
export const Gauge = base(<><path d="M12 14 16 9" /><path d="M4 18a9 9 0 1 1 16 0" /></>);
export const Check = base(<path d="m5 12 4.5 4.5L19 7" />);
export const Shield = base(<><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" /><path d="m9 12 2 2 4-4" /></>);
export const Upload = base(<><path d="M12 16V4M7 9l5-5 5 5" /><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" /></>);
export const Chat = base(<path d="M4 5h16v11H9l-5 4z" />);
export const Sparkle = base(<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" />);
export const Close = base(<path d="M6 6l12 12M18 6 6 18" />);
export const Wallet = base(<><rect x="3" y="6" width="18" height="14" rx="3" /><path d="M3 10h18M16 15h2" /></>);
export const Sun = base(<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>);
export const Moon = base(<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />);
export const Bell = base(<><path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8" /><path d="M10.3 20a2 2 0 0 0 3.4 0" /></>);
export const Printer = base(<><path d="M6 9V3h12v6" /><rect x="3" y="9" width="18" height="8" rx="2" /><path d="M6 14h12v7H6z" /></>);
export const Copy = base(<><rect x="9" y="9" width="12" height="12" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></>);
export const Refresh = base(<><path d="M20 11a8 8 0 1 0-2.3 5.7" /><path d="M20 4v7h-7" /></>);
export const Piggy = base(<><path d="M19 11c0-3.9-3.6-6-8-6S3 7.1 3 11c0 2.2 1.1 3.8 2.7 4.8L5 20h3.5l.8-2h4.4l.8 2H18l-.6-3.6A5 5 0 0 0 19 13h2v-3h-2z" /><path d="M15 9h.01" /></>);
export const Alert = base(<><path d="M12 3 2 21h20z" /><path d="M12 10v5M12 18h.01" /></>);
export const Info = base(<><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7.5h.01" /></>);
export const FileDoc = base(<><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></>);
export const Clock = base(<><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>);
export const UserIcon = base(<><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>);
export const LogOut = base(<><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" /><path d="M10 17l-5-5 5-5M5 12h11" /></>);
export const Folder = base(<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />);
export const Trash = base(<><path d="M4 7h16M10 11v6M14 11v6" /><path d="M6 7l1 13h10l1-13M9 7V4h6v3" /></>);
export const ArrowLeft = base(<path d="M19 12H5M11 18l-6-6 6-6" />);
export const Eye = base(<><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>);
