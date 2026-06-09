"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { site } from "@/lib/site";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-mist">
      <div className="absolute inset-0">
        <img
          src="/images/technology-workspace.svg"
          alt=""
          className="h-full w-full object-cover opacity-20"
        />
      </div>
      <div className="section-shell relative grid min-h-[calc(100vh-80px)] items-center gap-10 py-16 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-teal/30 bg-white px-4 py-2 text-sm font-bold text-teal shadow-sm">
            <CheckCircle2 size={17} />
            {site.name} · {site.tagline}
          </div>
          <h1 className="mt-7 text-4xl font-black leading-tight text-navy sm:text-5xl lg:text-6xl">
            Custom Software Development & Automation Solutions
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
            We build scalable software, API integrations, automation systems, dashboards, cloud
            infrastructure, and custom technology solutions for businesses and professionals.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/contact" className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-royal px-6 py-4 font-bold text-white shadow-soft transition hover:bg-navy">
              Schedule Consultation
              <ArrowRight size={18} />
            </Link>
            <Link href="/services" className="focus-ring inline-flex items-center justify-center rounded border border-slate-300 bg-white px-6 py-4 font-bold text-navy transition hover:border-royal hover:text-royal">
              Explore Services
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="hidden lg:block"
        >
          <div className="rounded border border-slate-200 bg-white/92 p-6 shadow-soft backdrop-blur">
            <div className="grid gap-4">
              {["Engineering", "Automation", "API Bridges", "Cloud Delivery"].map((label, index) => (
                <div key={label} className="flex items-center gap-4 rounded border border-slate-200 bg-mist p-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded bg-navy text-white font-black">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-extrabold text-navy">{label}</p>
                    <p className="text-sm text-slate-600">Enterprise-grade technology execution</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
