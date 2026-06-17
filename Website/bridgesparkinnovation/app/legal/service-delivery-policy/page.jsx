import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Service Delivery Policy",
  description: "Service delivery policy for Sparkbridge Innovations software development, automation, API integration, cloud deployment, support, and technical services.",
  path: "/legal/service-delivery-policy",
});

const sections = [
  {
    title: "Digital Service Delivery",
    body:
      "Sparkbridge Innovations provides software development, automation, API integration, dashboard, cloud deployment, support, maintenance, and technical services. No physical shipping is involved for these services.",
  },
  {
    title: "Delivery Method",
    body:
      "Services are delivered digitally through email, deployment, online access, consultation, documentation, remote support, or agreed project milestones based on the confirmed scope of work.",
  },
  {
    title: "Delivery Timeline",
    body:
      "Delivery timelines depend on the selected service, project complexity, client approvals, required access, third-party platform availability, and the agreed proposal, invoice, or statement of work.",
  },
  {
    title: "Client Coordination",
    body:
      "Clients must provide accurate requirements, approvals, credentials, content, feedback, and other information required for successful delivery. Delays in client inputs may affect the delivery schedule.",
  },
  {
    title: "Completion",
    body:
      "A service may be considered delivered when the agreed work is shared, deployed, activated, demonstrated, handed over, or made available through the agreed digital channel.",
  },
];

export default function ServiceDeliveryPolicyPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Service Delivery Policy"
        description="This policy explains how Sparkbridge Innovations delivers software, automation, integration, support, and technical services."
      />
      <section className="bg-white py-14">
        <div className="section-shell legal-content max-w-4xl text-justify">
          {sections.map((section) => (
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
