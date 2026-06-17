import { CardGrid } from "@/components/CardGrid";
import { CTA } from "@/components/CTA";
import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";
import { services } from "@/lib/site";

export const metadata = pageMetadata({
  title: "Services",
  description: "Python software development, API integration, API bridging, custom automation script development, third-party API integration, dashboards, databases, cloud deployment, and technical support.",
  path: "/services",
});

export default function ServicesPage() {
  return (
    <>
      <PageHero
        eyebrow="Services"
        title="Professional software development and automation services."
        description="We design and build scalable software, secure integrations, API bridges, dashboards, automation systems, cloud infrastructure, and support workflows."
      />
      <section className="bg-white py-16">
        <div className="section-shell">
          <CardGrid items={services} />
        </div>
      </section>
      <CTA />
    </>
  );
}
