import { site } from "@/lib/site";

const routes = [
  "",
  "/about",
  "/services",
  "/products",
  "/checkout",
  "/contact",
  "/legal/disclaimer",
  "/legal/terms-and-conditions",
  "/legal/refund-policy",
  "/legal/cancellation-policy",
  "/legal/service-delivery-policy",
  "/legal/privacy-policy",
];

export default function sitemap() {
  return routes.map((route) => ({
    url: `${site.url}${route}`,
    lastModified: new Date("2026-06-08"),
    changeFrequency: route ? "monthly" : "weekly",
    priority: route ? 0.7 : 1,
  }));
}
