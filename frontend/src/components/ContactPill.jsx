/**
 * ContactPill - Styled link component for contact information
 * Used for email and social media links in header/footer
 */
export const ContactPill = ({ href, icon, text }) => (
  <a
    href={href}
    target="_blank"
    rel="noopener noreferrer"
    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100/50 border border-slate-200/50 hover:bg-slate-100 hover:border-slate-300 transition-all duration-200 text-sm text-slate-700 hover:text-slate-900"
  >
    {icon}
    <span className="hidden sm:inline">{text}</span>
  </a>
);
