import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Privacy Policy",
  description: "Privacy policy for Sparkbridge Innovations covering information collection, contact form submissions, data storage, data retention, security practices, user rights, cookies, and communication preferences.",
  path: "/legal/privacy-policy",
});

const sections = [
  {
    title: "Information Collection",
    body: "We may collect information that users voluntarily submit, including name, mobile number, email address, service requirement, message content, and related communication details.",
  },
  {
    title: "Contact Form Submissions",
    body: "Contact form submissions are used to understand enquiries, respond to service requests, schedule consultations, and maintain business communication records.",
  },
  {
    title: "Data Storage",
    body: "Submitted information may be stored in secure application storage, business systems, or communication tools used by Sparkbridge Innovations for enquiry management and support.",
  },
  {
    title: "Data Retention Policy",
    body: "We retain submitted personal and business information only for as long as necessary to respond to enquiries, provide requested services, maintain business and support records, comply with legal, tax, accounting, and regulatory obligations, resolve disputes, and enforce agreements. When information is no longer required, we may securely delete, anonymize, or archive it in accordance with applicable requirements and internal business needs.",
  },
  {
    title: "Security Practices",
    body: "We use reasonable administrative, technical, and operational safeguards to protect submitted information from unauthorized access, misuse, alteration, or disclosure.",
  },
  {
    title: "User Rights",
    body: "Users may request access, correction, or deletion of their submitted information by contacting Sparkbridge Innovations through the official contact channel.",
  },
  {
    title: "Cookie Usage",
    body: "The website may use essential cookies or analytics technologies to improve site performance, user experience, security, and service quality.",
  },
  {
    title: "Communication Preferences",
    body: "Users may opt out of non-essential business communications. Service-related, enquiry-related, and support communications may continue where necessary.",
  },
];

export default function PrivacyPolicyPage() {
  return (
    <>
      <PageHero eyebrow="Legal" title="Privacy Policy" description="This policy explains how Sparkbridge Innovations handles information submitted through the website and related communication channels." />
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
