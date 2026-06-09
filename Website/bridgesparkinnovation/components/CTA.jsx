import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function CTA() {
  return (
    <section className="bg-navy py-14 text-white">
      <div className="section-shell flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">Your Tech Assistant</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Build the software your workflow needs.</h2>
          <p className="mt-4 max-w-2xl leading-7 text-slate-300">
            Share your process, product idea, integration requirement, or automation goal. We will help shape it into a practical technology roadmap.
          </p>
        </div>
        <Link href="/contact" className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-white px-6 py-4 font-bold text-navy transition hover:bg-teal hover:text-white">
          Schedule Consultation
          <ArrowRight size={18} />
        </Link>
      </div>
    </section>
  );
}
