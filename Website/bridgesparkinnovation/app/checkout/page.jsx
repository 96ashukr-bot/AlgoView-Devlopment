import { Suspense } from "react";
import { CheckoutForm } from "@/components/CheckoutForm";
import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Checkout",
  description: "Submit a checkout enquiry for Sparkbridge Innovations products and technology platforms.",
  path: "/checkout",
});

export default function CheckoutPage() {
  return (
    <>
      <PageHero
        eyebrow="Checkout"
        title="Submit your product checkout enquiry."
        description="Share your billing and contact details for the selected product. Our team will verify the requirement and connect with you for next steps."
      />
      <section className="bg-white py-16">
        <div className="section-shell grid gap-8 lg:grid-cols-[0.8fr_1.2fr]">
          <aside className="rounded border border-slate-200 bg-mist p-6">
            <h2 className="text-2xl font-black text-navy">Before checkout</h2>
            <p className="mt-4 leading-7 text-slate-700">
              This page collects customer and billing details for product enquiries. Final pricing, implementation scope, activation, support plan, and payment instructions will be confirmed by Sparkbridge Innovations after review.
            </p>
          </aside>
          <Suspense fallback={<div className="rounded border border-slate-200 bg-white p-7 text-slate-600">Loading checkout...</div>}>
            <CheckoutForm />
          </Suspense>
        </div>
      </section>
    </>
  );
}
