import { PageHero } from "@/components/PageHero";
import { disclaimerSections } from "@/lib/legal";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Disclaimer",
  description: "Disclaimer for Sparkbridge Innovations website, software development services, automation systems, API integrations, third-party dependencies, and technology solutions.",
  path: "/legal/disclaimer",
});

export default function DisclaimerPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Disclaimer"
        description="This disclaimer explains the limits of website information, software implementation, third-party dependencies, and technology outcomes."
      />
      <section className="bg-white py-14">
        <div className="section-shell legal-content max-w-4xl text-justify">
          {disclaimerSections.map((section) => (
            <section key={section.title}>
              <h2>{section.title}</h2>
              <p>{section.body}</p>
            </section>
          ))}
        </div>
      </section>
    </>
  );
}
