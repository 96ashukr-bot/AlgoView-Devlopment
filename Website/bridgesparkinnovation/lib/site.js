import {
  Blocks,
  Bot,
  Cloud,
  Code2,
  Database,
  Headphones,
  Layers3,
  LineChart,
  LockKeyhole,
  Network,
  Rocket,
  ServerCog,
  ShieldCheck,
  Workflow,
} from "lucide-react";

export const site = {
  name: "Sparkbridge Innovations",
  tagline: "Your Tech Assistant",
  domain: "bridgesparkinnovation.com",
  url: "https://bridgesparkinnovation.com",
  description:
    "Sparkbridge Innovations builds custom software, API integrations, automation systems, dashboards, cloud infrastructure, and digital products for businesses and professionals.",
  email: "support@bridgesparkinnovation.com",
  phone: "8586078471",
  address: "2nd Floor, B-56, Sector 64, Noida, Uttar Pradesh 201301",
  gst: "09EOFPB1620N1ZZ",
};

export const navLinks = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/services" },
  { label: "Products", href: "/products" },
  { label: "Contact", href: "/contact" },
];

export const services = [
  {
    title: "Python Software Development",
    slug: "python-software-development",
    price: "INR 25,000/- onwards",
    description:
      "Custom backend systems, automation platforms, enterprise software, workflow tools, and scalable applications.",
    icon: Code2,
  },
  {
    title: "API Development & Integration",
    slug: "api-development-integration",
    price: "INR 7,000/- onwards",
    description:
      "Secure API creation, integration, middleware solutions, and connectivity between platforms.",
    icon: Network,
  },
  {
    title: "API Bridging Solutions",
    slug: "api-bridging-solutions",
    price: "INR 7,000/- onwards",
    description: "Custom API bridge development to connect multiple applications and services.",
    icon: Workflow,
  },
  {
    title: "Custom Automation Script Development",
    slug: "custom-automation-script-development",
    price: "INR 15,000/- onwards",
    description:
      "Custom scripts, alerts, dashboards, and automation workflows.",
    icon: LineChart,
  },
  {
    title: "Third-Party API Integration",
    slug: "third-party-api-integration",
    price: "INR 18,000/- onwards",
    description: "Integration of third-party APIs for automation, reporting, and workflow management.",
    icon: Blocks,
  },
  {
    title: "Automation Software",
    slug: "automation-software",
    price: "INR 40,000/- onwards",
    description:
      "Client-defined automation systems, execution workflows, monitoring tools, and process automation.",
    icon: Bot,
  },
  {
    title: "Dashboard Development",
    slug: "dashboard-development",
    price: "INR 18,000/- onwards",
    description: "Interactive dashboards for reporting, analytics, monitoring, and operational management.",
    icon: Layers3,
  },
  {
    title: "Cloud Deployment",
    slug: "cloud-deployment",
    price: "INR 20,000/- onwards",
    description: "AWS infrastructure setup, cloud architecture, monitoring, optimization, and deployment.",
    icon: Cloud,
  },
  {
    title: "Database Development",
    slug: "database-development",
    price: "INR 21,000/- onwards",
    description: "PostgreSQL, MySQL, database architecture, optimization, and maintenance.",
    icon: Database,
  },
  {
    title: "Technical Support & Maintenance",
    slug: "technical-support-maintenance",
    price: "INR 5,000/- onwards",
    description: "Ongoing maintenance, upgrades, monitoring, troubleshooting, and technical support.",
    icon: Headphones,
  },
];

export const products = [
  {
    title: "Automation Platform",
    slug: "automation-platform",
    price: "INR 40,000/- onwards",
    description:
      "Multi-user software platform supporting automation, workflow management, reporting, API integrations, and operational control.",
  },
  {
    title: "API Bridge Engine",
    slug: "api-bridge-engine",
    price: "INR 15,000/- onwards",
    description: "Reliable middleware platform connecting multiple APIs and software systems.",
  },
  {
    title: "Automation Suite",
    slug: "automation-suite",
    price: "INR 10,000/- onwards",
    description: "Technology platform for automating client-defined workflows and execution logic.",
  },
  {
    title: "Strategy Deployment System",
    slug: "strategy-deployment-system",
    price: "INR 7,000/- onwards",
    description: "Centralized platform for deploying and managing automation strategies and logic.",
  },
  {
    title: "Data Integration Engine",
    slug: "data-integration-engine",
    price: "INR 25,000/- onwards",
    description: "Centralized real-time data integration collection, processing, monitoring, and distribution system.",
  },
  {
    title: "Client Support Portal",
    slug: "client-support-portal",
    price: "INR 35,000/- onwards",
    description: "Role-based communication and support management platform for clients and administrators.",
  },
];

export const productOptions = products.map((product) => product.title);
export const serviceOptions = services.map((service) => service.title);
export const checkoutOptions = [...productOptions, ...serviceOptions];

export function getProductBySlug(slug) {
  return products.find((product) => product.slug === slug);
}

export function getServiceBySlug(slug) {
  return services.find((service) => service.slug === slug);
}

export function getCheckoutItemBySlug(slug) {
  return getProductBySlug(slug) || getServiceBySlug(slug);
}

export const reasons = [
  { title: "Custom Development", icon: Code2 },
  { title: "Scalable Architecture", icon: ServerCog },
  { title: "Secure Solutions", icon: LockKeyhole },
  { title: "Cloud Ready", icon: Cloud },
  { title: "API Expertise", icon: Network },
  { title: "Dedicated Support", icon: Headphones },
  { title: "Enterprise Reliability", icon: ShieldCheck },
  { title: "Technology Partnership", icon: Rocket },
];
