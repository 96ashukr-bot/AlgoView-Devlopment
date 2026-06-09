import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { pageMetadata } from "@/lib/seo";
import { site } from "@/lib/site";

export const metadata = pageMetadata({
  description:
    "Custom Software Development, API Integrations, Automation Systems, TradingView Pine Script Development, Broker API Integration, Cloud Deployment, Dashboard Development, and Technology Solutions.",
});

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: site.name,
              url: site.url,
              slogan: site.tagline,
              description: site.description,
              contactPoint: {
                "@type": "ContactPoint",
                contactType: "customer support",
                email: site.email,
              },
            }),
          }}
        />
      </body>
    </html>
  );
}
