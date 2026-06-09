import { site } from "@/lib/site";

export function pageMetadata({ title, description, path = "/" }) {
  const pageTitle = title ? `${title} | ${site.name}` : `${site.name} | ${site.tagline}`;
  const pageDescription = description || site.description;
  const url = `${site.url}${path}`;

  return {
    title: pageTitle,
    description: pageDescription,
    alternates: {
      canonical: url,
    },
    openGraph: {
      title: pageTitle,
      description: pageDescription,
      url,
      siteName: site.name,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: pageTitle,
      description: pageDescription,
    },
  };
}
