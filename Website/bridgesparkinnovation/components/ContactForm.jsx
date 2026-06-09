"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { serviceOptions } from "@/lib/site";

const initialState = {
  name: "",
  mobile: "",
  email: "",
  service: serviceOptions[0],
  message: "",
};

export function ContactForm() {
  const [form, setForm] = useState(initialState);
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitForm(event) {
    event.preventDefault();
    setSubmitting(true);
    setStatus({ type: "idle", message: "" });

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Please check the details and try again.");
      }

      setForm(initialState);
      setStatus({
        type: "success",
        message: "Thank you for contacting Sparkbridge Innovations. Our team will connect with you shortly.",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submitForm} className="rounded border border-slate-200 bg-white p-5 shadow-soft sm:p-7">
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold text-navy">
          Name
          <input
            required
            name="name"
            value={form.name}
            onChange={updateField}
            className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink"
            autoComplete="name"
          />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Mobile Number
          <input
            required
            name="mobile"
            value={form.mobile}
            onChange={updateField}
            className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink"
            autoComplete="tel"
            inputMode="tel"
          />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Email Address
          <input
            required
            type="email"
            name="email"
            value={form.email}
            onChange={updateField}
            className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink"
            autoComplete="email"
          />
        </label>
        <label className="grid gap-2 text-sm font-bold text-navy">
          Service Required
          <select
            name="service"
            value={form.service}
            onChange={updateField}
            className="focus-ring rounded border border-slate-300 px-4 py-3 font-normal text-ink"
          >
            {serviceOptions.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>
      <label className="mt-5 grid gap-2 text-sm font-bold text-navy">
        Message
        <textarea
          required
          name="message"
          value={form.message}
          onChange={updateField}
          className="focus-ring min-h-36 rounded border border-slate-300 px-4 py-3 font-normal text-ink"
        />
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="focus-ring mt-6 inline-flex w-full items-center justify-center gap-2 rounded bg-royal px-6 py-4 font-bold text-white shadow-soft transition hover:bg-navy disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
      >
        <Send size={18} />
        {submitting ? "Submitting..." : "Submit Enquiry"}
      </button>
      {status.message && (
        <p className={`mt-5 rounded border px-4 py-3 text-sm font-semibold ${status.type === "success" ? "border-teal/30 bg-teal/10 text-teal" : "border-red-200 bg-red-50 text-red-700"}`}>
          {status.message}
        </p>
      )}
    </form>
  );
}
