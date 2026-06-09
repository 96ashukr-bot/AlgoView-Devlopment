export function CardGrid({ items, columns = "lg:grid-cols-3", renderAction }) {
  return (
    <div className={`grid gap-5 sm:grid-cols-2 ${columns}`}>
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <article key={item.title} className="rounded border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-soft">
            {Icon && (
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded bg-teal/10 text-teal">
                <Icon size={24} />
              </div>
            )}
            <h3 className="text-lg font-extrabold text-navy">{item.title}</h3>
            {item.description && <p className="mt-3 text-sm leading-7 text-slate-600">{item.description}</p>}
            {renderAction && <div className="mt-5">{renderAction(item)}</div>}
          </article>
        );
      })}
    </div>
  );
}
