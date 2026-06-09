export function PageHero({ eyebrow, title, description }) {
  return (
    <section className="border-b border-slate-200 bg-mist py-16">
      <div className="section-shell">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">{eyebrow}</p>
        <h1 className="mt-4 max-w-4xl text-4xl font-black leading-tight text-navy sm:text-5xl">{title}</h1>
        {description && <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-700">{description}</p>}
      </div>
    </section>
  );
}
