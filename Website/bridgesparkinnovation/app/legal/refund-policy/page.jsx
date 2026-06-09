import { PageHero } from "@/components/PageHero";
import { refundSections } from "@/lib/legal";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Refund Policy",
  description: "Refund policy for Sparkbridge Innovations custom software development, automation, API integration, cloud deployment, consulting, support, maintenance, and technical services.",
  path: "/legal/refund-policy",
});

export default function RefundPolicyPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Refund Policy"
        description="This policy explains how refunds are handled for custom software development, automation, integration, support, maintenance, and technology services."
      />
      <section className="bg-white py-14">
        <div className="section-shell legal-content max-w-4xl text-justify">
          <p>
            Sparkbridge Innovations provides customized software and technical services that involve planning, engineering time, infrastructure setup, implementation effort, third-party coordination, and ongoing support allocation.
          </p>
          {refundSections.map((section) => (
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
