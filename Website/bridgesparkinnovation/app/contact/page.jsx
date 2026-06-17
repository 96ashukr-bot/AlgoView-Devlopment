import { Mail, MapPin, Phone } from "lucide-react";
import { ContactForm } from "@/components/ContactForm";
import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";
import { site } from "@/lib/site";

export const metadata = pageMetadata({
  title: "Contact",
  description: "Contact Sparkbridge Innovations for custom software development, automation systems, API integrations, dashboards, cloud deployment, and technical support.",
  path: "/contact",
});

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="Tell us what you want to build."
        description="Share your software, automation, dashboard, cloud, or integration requirement. Our team will connect with you shortly."
      />
      <section className="bg-white py-16">
        <div className="section-shell grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <aside className="rounded border border-slate-200 bg-mist p-6">
            <h2 className="text-2xl font-black text-navy">{site.name}</h2>
            <p className="mt-2 text-sm font-bold uppercase tracking-[0.18em] text-teal">{site.tagline}</p>
            <div className="mt-8 grid gap-5 text-slate-700">
              <p className="flex items-center gap-3">
                <Mail className="text-teal" size={20} />
                {site.email}
              </p>
              <p className="flex items-center gap-3">
                <Phone className="text-teal" size={20} />
                {site.phone}
              </p>
              <p className="flex items-center gap-3">
                <MapPin className="text-teal" size={20} />
                {site.address}
              </p>
            </div>
            <p className="mt-8 text-sm leading-7 text-slate-600">
              Sparkbridge Innovations is an Information Technology and Software Development Company. We build software and automation solutions based on client requirements.
            </p>
          </aside>
          <ContactForm />
        </div>
      </section>
    </>
  );
}
