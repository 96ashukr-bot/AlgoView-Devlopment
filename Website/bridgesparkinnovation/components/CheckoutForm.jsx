"use client";

import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { CheckCircle2, Send } from "lucide-react";
import { getProductBySlug, productOptions } from "@/lib/site";

const emptyForm = {
  name: "",
  email: "",
  contactNumber: "",
  amount: "",
  companyName: "",
  address: "",
  city: "",
  state: "",
  pinCode: "",
  gstNumber: "",
  notes: "",
};

export function CheckoutForm() {
  const searchParams = useSearchParams();
  const selectedProduct = useMemo(() => {
    const product = getProductBySlug(searchParams.get("product"));
    return product?.title || productOptions[0];
  }, [searchParams]);

  const [product, setProduct] = useState(selectedProduct);
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitCheckout(event) {
    event.preventDefault();
    setSubmitting(true);
    setStatus({ type: "idle", message: "" });

    try {
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product, ...form }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Please check the checkout details and try again.");
      }

      setForm(emptyForm);
      setStatus({
        type: "success",
        message: "Thank you. Your checkout enquiry has been submitted. Our team will connect with you shortly.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submitCheckout} className="rounded border border-slate-200 bg-white p-5 shadow-soft sm:p-7">
      <label className="grid gap-2 text-sm font-bold text-navy">
        Product
        <select
          value={product}
          onChange={(event) => setProduct(event.target.value)}
          className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink"
        >
          {productOptions.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      </label>

      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold text-navy">
          Customer Name
          <input required name="name" value={form.name} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="name" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Email Address
          <input required type="email" name="email" value={form.email} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="email" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Contact Number
          <input required name="contactNumber" value={form.contactNumber} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="tel" inputMode="tel" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Amount
          <input required name="amount" value={form.amount} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" inputMode="decimal" placeholder="Amount in INR" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Company Name
          <input name="companyName" value={form.companyName} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="organization" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy sm:col-span-2">
          Address
          <textarea required name="address" value={form.address} onChange={updateField} className="focus-ring min-h-28 rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="street-address" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          City
          <input required name="city" value={form.city} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="address-level2" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          State
          <input required name="state" value={form.state} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="address-level1" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          PIN Code
          <input required name="pinCode" value={form.pinCode} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" autoComplete="postal-code" inputMode="numeric" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          GST Number
          <input name="gstNumber" value={form.gstNumber} onChange={updateField} className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink" />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy sm:col-span-2">
          Notes / Requirement
          <textarea name="notes" value={form.notes} onChange={updateField} className="focus-ring min-h-28 rounded border border-slate-300 px-4 py-3 font-normal text-ink" />
        </label>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="focus-ring mt-6 inline-flex w-full items-center justify-center gap-2 rounded bg-royal px-6 py-4 font-bold text-white shadow-soft transition hover:bg-navy disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
      >
        <Send size={18} />
        {submitting ? "Submitting..." : "Submit Checkout Enquiry"}
      </button>
      {status.message && (
        <p className={`mt-5 flex items-start gap-2 rounded border px-4 py-3 text-sm font-semibold ${status.type === "success" ? "border-teal/30 bg-teal/10 text-teal" : "border-red-200 bg-red-50 text-red-700"}`}>
          {status.type === "success" && <CheckCircle2 className="mt-0.5 shrink-0" size={17} />}
          {status.message}
        </p>
      )}
    </form>
  );
}
