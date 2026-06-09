"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { navLinks, site } from "@/lib/site";

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="section-shell flex h-20 items-center justify-between">
        <Link href="/" className="focus-ring flex min-w-0 items-center gap-3" aria-label="Sparkbridge Innovations home">
          <img
            src="/images/logo.png"
            alt="Sparkbridge Innovations - Your Tech Assistant"
            className="h-14 w-14 rounded-full object-contain sm:h-16 sm:w-16"
          />
          <span className="min-w-0">
            <span className="block text-sm font-extrabold leading-tight text-navy sm:text-lg">{site.name}</span>
            <span className="block text-[10px] font-semibold uppercase leading-tight tracking-[0.18em] text-teal sm:text-xs">
              {site.tagline}
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Main navigation">
          {navLinks.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`focus-ring text-sm font-semibold transition ${active ? "text-royal" : "text-slate-700 hover:text-navy"}`}
              >
                {link.label}
              </Link>
            );
          })}
          <Link
            href="/contact"
            className="focus-ring rounded bg-royal px-5 py-3 text-sm font-bold text-white shadow-soft transition hover:bg-navy"
          >
            Schedule Consultation
          </Link>
        </nav>

        <button
          type="button"
          className="focus-ring inline-flex h-11 w-11 items-center justify-center rounded border border-slate-200 text-navy lg:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-label="Toggle navigation"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-white lg:hidden">
          <nav className="section-shell grid gap-1 py-4" aria-label="Mobile navigation">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="focus-ring rounded px-3 py-3 text-sm font-semibold text-slate-700 hover:bg-mist hover:text-navy"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
