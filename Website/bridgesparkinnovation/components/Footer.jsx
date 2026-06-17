import Link from "next/link";
import { navLinks, site } from "@/lib/site";

const legalLinks = [
  { label: "Terms & Conditions", href: "/legal/terms-and-conditions" },
  { label: "Refund Policy", href: "/legal/refund-policy" },
  { label: "Cancellation Policy", href: "/legal/cancellation-policy" },
  { label: "Service Delivery Policy", href: "/legal/service-delivery-policy" },
  { label: "Disclaimer", href: "/legal/disclaimer" },
  { label: "Privacy Policy", href: "/legal/privacy-policy" },
];

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-navy text-white">
      <div className="section-shell grid gap-10 py-12 lg:grid-cols-[1.2fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-4">
            <div className="inline-flex rounded bg-white px-4 py-3">
              <img
                src="/images/logo.png"
                alt="Sparkbridge Innovations - Your Tech Assistant"
                className="h-20 w-20 rounded-full object-contain sm:h-24 sm:w-24"
              />
            </div>
            <div>
              <p className="text-lg font-extrabold">{site.name}</p>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal">{site.tagline}</p>
            </div>
          </div>
          <p className="mt-5 max-w-md text-sm leading-7 text-slate-300">
            Information Technology and Software Development Company building automation, API integrations,
            dashboards, cloud infrastructure, and custom digital products.
          </p>
          <p className="mt-4 text-sm font-semibold text-slate-300">GST: {site.gst}</p>
        </div>

        <div>
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-slate-300">Company</p>
          <div className="mt-4 grid gap-3">
            {navLinks.map((link) => (
              <Link key={link.href} href={link.href} className="text-sm text-slate-300 hover:text-white">
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-slate-300">Legal</p>
          <div className="mt-4 grid gap-3">
            {legalLinks.map((link) => (
              <Link key={link.href} href={link.href} className="text-sm text-slate-300 hover:text-white">
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="section-shell flex flex-col gap-3 py-5 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} {site.name}. All rights reserved.</p>
          <p>{site.domain}</p>
        </div>
      </div>
    </footer>
  );
}
