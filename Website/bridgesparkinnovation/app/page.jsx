import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { CardGrid } from "@/components/CardGrid";
import { CTA } from "@/components/CTA";
import { Hero } from "@/components/Hero";
import { SectionHeader } from "@/components/SectionHeader";
import { products, reasons, services } from "@/lib/site";

export default function HomePage() {
  return (
    <>
      <Hero />
      <section className="bg-white py-16">
        <div className="section-shell">
          <SectionHeader
            eyebrow="Technology services"
            title="Engineering support for automation, integrations, and digital products."
            description="Sparkbridge Innovations works as a technology partner for businesses, professionals, traders, startups, agencies, and organizations that need reliable custom software."
          />
          <CardGrid items={services.slice(0, 6)} />
          <div className="mt-8">
            <Link href="/services" className="focus-ring inline-flex items-center gap-2 rounded border border-slate-300 px-5 py-3 font-bold text-navy transition hover:border-royal hover:text-royal">
              View all services
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      <section className="bg-mist py-16">
        <div className="section-shell grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <SectionHeader
              eyebrow="Why choose us"
              title="Built for practical delivery and long-term reliability."
              description="We focus on secure architecture, clear implementation, and maintainable software that supports real operational workflows."
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {reasons.map((reason) => {
              const Icon = reason.icon;
              return (
                <div key={reason.title} className="flex items-center gap-4 rounded border border-slate-200 bg-white p-5 shadow-sm">
                  <span className="flex h-11 w-11 items-center justify-center rounded bg-teal/10 text-teal">
                    <Icon size={22} />
                  </span>
                  <p className="font-extrabold text-navy">{reason.title}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="section-shell">
          <SectionHeader
            eyebrow="Product capability"
            title="Platforms and engines for modern workflow automation."
            description="Our products are built around API connectivity, operational control, reporting, monitoring, and client-defined automation."
          />
          <CardGrid items={products.slice(0, 3)} />
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/products" className="focus-ring inline-flex items-center gap-2 rounded bg-royal px-5 py-3 font-bold text-white transition hover:bg-navy">
              Explore products
              <ArrowRight size={18} />
            </Link>
            <Link href="/legal/disclaimer" className="focus-ring inline-flex items-center gap-2 rounded border border-slate-300 px-5 py-3 font-bold text-navy transition hover:border-royal hover:text-royal">
              <CheckCircle2 size={18} />
              Compliance notice
            </Link>
          </div>
        </div>
      </section>
      <CTA />
    </>
  );
}
