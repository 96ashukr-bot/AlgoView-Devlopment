import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Cancellation Policy",
  description: "Cancellation policy for Sparkbridge Innovations custom software development, automation, API integration, cloud deployment, support, maintenance, and technical services.",
  path: "/legal/cancellation-policy",
});

const sections = [
  {
    title: "Cancellation Before Work Starts",
    body:
      "Clients may request cancellation before project work, implementation, activation, consultation, support allocation, or resource assignment has started. Such requests will be reviewed based on the confirmed proposal, invoice, and service scope.",
  },
  {
    title: "Cancellation After Work Starts",
    body:
      "Once work has started, resources have been allocated, service access has been provided, consultation has begun, or implementation activity has started, cancellation may not be available for the active scope of work.",
  },
  {
    title: "Custom Software and Technical Services",
    body:
      "Custom software development, automation, API integration, dashboard development, cloud deployment, support, maintenance, and technical consulting services involve planning, engineering time, and resource allocation. Cancellation eligibility is therefore assessed according to completed work and committed resources.",
  },
  {
    title: "Subscriptions and Support Plans",
    body:
      "For subscription, hosting assistance, maintenance, monitoring, or support plans, cancellation requests generally apply to future billing cycles. Charges for the active billing period are not cancelled unless separately agreed in writing.",
  },
  {
    title: "How to Request Cancellation",
    body:
      "Cancellation requests must be sent in writing to support@bridgesparkinnovation.com with the client name, contact details, invoice or project reference, and reason for cancellation. Sparkbridge Innovations will review the request and respond through the official communication channel.",
  },
  {
    title: "Relation to Refund Policy",
    body:
      "Cancellation approval does not automatically mean a refund is due. Refund handling is governed by the Refund Policy, the agreed proposal, invoice terms, and the stage of service delivery.",
  },
];

export default function CancellationPolicyPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Cancellation Policy"
        description="This policy explains how cancellation requests are handled for software, automation, integration, support, and technical services."
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
