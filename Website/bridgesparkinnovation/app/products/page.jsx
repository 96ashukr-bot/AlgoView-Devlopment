import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { CardGrid } from "@/components/CardGrid";
import { CTA } from "@/components/CTA";
import { PageHero } from "@/components/PageHero";
import { pageMetadata } from "@/lib/seo";
import { products } from "@/lib/site";

export const metadata = pageMetadata({
  title: "Products",
  description: "Software platforms from Sparkbridge Innovations including AlgoView Platform, API Bridge Engine, Trading Automation Suite, Strategy Deployment System, Market Data Engine, and Client Support Portal.",
  path: "/products",
});

export default function ProductsPage() {
  return (
    <>
      <PageHero
        eyebrow="Products"
        title="Technology platforms for automation, integrations, and operational control."
        description="Our product capability helps clients manage workflows, reporting, API connectivity, support, monitoring, and client-defined automation logic."
      />
      <section className="bg-white py-16">
        <div className="section-shell">
          <CardGrid
            items={products}
            columns="lg:grid-cols-2"
            renderAction={(product) => (
              <Link
                href={`/checkout?product=${product.slug}`}
                className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-royal px-4 py-3 text-sm font-bold text-white transition hover:bg-navy"
              >
                <ShoppingCart size={17} />
                Checkout
              </Link>
            )}
          />
        </div>
      </section>
      <CTA />
    </>
  );
}
