import { PageHero } from "@/components/PageHero";
import { termsSections } from "@/lib/legal";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Terms & Conditions",
  description: "Terms and conditions for using Sparkbridge Innovations website, services, software development, automation, API integration, support, and technology solutions.",
  path: "/legal/terms-and-conditions",
});

export default function TermsPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Terms & Conditions"
        description="These terms explain the general conditions for using this website and engaging Sparkbridge Innovations for software development, automation, integration, support, and technology services."
      />
      <section className="bg-white py-14">
        <div className="section-shell max-w-4xl">
          <div className="mb-8 grid gap-3 rounded border border-slate-200 bg-mist p-5 text-sm text-slate-700 sm:grid-cols-2">
            <p>
              <strong className="text-navy">Terms Version:</strong> v1
            </p>
            <p>
              <strong className="text-navy">Last Updated Date:</strong> 8 June 2026
            </p>
          </div>
          <article className="legal-content rounded border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
            <p>
              These Terms & Conditions apply to users who visit this website, submit enquiries, request consultations, or engage Sparkbridge Innovations for technology services.
            </p>
            {termsSections.map((section) => (
              <section key={section.title}>
                <h2>{section.title}</h2>
                <p>{section.body}</p>
              </section>
            ))}
          </article>
        </div>
      </section>
    </>
  );
}
