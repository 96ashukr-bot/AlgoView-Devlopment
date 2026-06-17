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
    description:
      "Custom backend systems, automation platforms, enterprise software, workflow tools, and scalable applications.",
    icon: Code2,
  },
  {
    title: "API Development & Integration",
    description:
      "Secure API creation, integration, middleware solutions, and connectivity between platforms.",
    icon: Network,
  },
  {
    title: "API Bridging Solutions",
    description: "Custom API bridge development to connect multiple applications and services.",
    icon: Workflow,
  },
  {
    title: "Custom Automation Script Development",
    description:
      "Custom scripts, alerts, dashboards, and automation workflows.",
    icon: LineChart,
  },
  {
    title: "Third-Party API Integration",
    description: "Integration of third-party APIs for automation, reporting, and workflow management.",
    icon: Blocks,
  },
  {
    title: "Automation Software",
    description:
      "Client-defined automation systems, execution workflows, monitoring tools, and process automation.",
    icon: Bot,
  },
  {
    title: "Dashboard Development",
    description: "Interactive dashboards for reporting, analytics, monitoring, and operational management.",
    icon: Layers3,
  },
  {
    title: "Cloud Deployment",
    description: "AWS infrastructure setup, cloud architecture, monitoring, optimization, and deployment.",
    icon: Cloud,
  },
  {
    title: "Database Development",
    description: "PostgreSQL, MySQL, database architecture, optimization, and maintenance.",
    icon: Database,
  },
  {
    title: "Technical Support & Maintenance",
    description: "Ongoing maintenance, upgrades, monitoring, troubleshooting, and technical support.",
    icon: Headphones,
  },
];

export const products = [
  {
    title: "Automation Platform",
    slug: "automation-platform",
    description:
      "Multi-user software platform supporting automation, workflow management, reporting, API integrations, and operational control.",
  },
  {
    title: "API Bridge Engine",
    slug: "api-bridge-engine",
    description: "Reliable middleware platform connecting multiple APIs and software systems.",
  },
  {
    title: "Automation Suite",
    slug: "automation-suite",
    description: "Technology platform for automating client-defined workflows and execution logic.",
  },
  {
    title: "Strategy Deployment System",
    slug: "strategy-deployment-system",
    description: "Centralized platform for deploying and managing automation strategies and logic.",
  },
  {
    title: "Data Integration Engine",
    slug: "data-integration-engine",
    description: "Centralized real-time data integration collection, processing, monitoring, and distribution system.",
  },
  {
    title: "Client Support Portal",
    slug: "client-support-portal",
    description: "Role-based communication and support management platform for clients and administrators.",
  },
];

export const productOptions = products.map((product) => product.title);

export function getProductBySlug(slug) {
  return products.find((product) => product.slug === slug);
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

export const serviceOptions = [
  "Python Software Development",
  "API Development & Integration",
  "API Bridging Solutions",
  "Custom Automation Script Development",
  "Third-Party API Integration",
  "Automation Software",
  "Dashboard Development",
  "Cloud Deployment",
  "Database Development",
  "Technical Support & Maintenance",
];
