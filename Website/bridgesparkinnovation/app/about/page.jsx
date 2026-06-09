import { CTA } from "@/components/CTA";
import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "About",
  description: "About Sparkbridge Innovations, an IT and software development company focused on automation, integrations, cloud infrastructure, and scalable digital products.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About us"
        title="About Sparkbridge Innovations"
        description="Sparkbridge Innovations is a software development company focused on building reliable technology solutions, automation systems, integrations, cloud infrastructure, and scalable digital products."
      />
      <section className="bg-white py-16">
        <div className="section-shell grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">Your Tech Assistant</p>
            <h2 className="mt-4 text-3xl font-black text-navy">Technology partnership for real business workflows.</h2>
          </div>
          <div className="space-y-6 text-lg leading-8 text-slate-700">
            <p>
              As Your Tech Assistant, we help businesses and professionals streamline operations through modern software engineering and intelligent automation.
            </p>
            <p>
              Our mission is to transform ideas into practical technology solutions that improve efficiency, productivity, and growth.
            </p>
            <p>
              We serve businesses, consultants, agencies, professional traders, fintech startups, and organizations that need secure software, API integrations, cloud deployment, dashboards, and ongoing technical support.
            </p>
          </div>
        </div>
      </section>
      <CTA />
    </>
  );
}
