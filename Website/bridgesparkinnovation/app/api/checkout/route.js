import fs from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";
import { checkoutOptions } from "@/lib/site";

const storageFile = path.join(process.cwd(), "storage", "checkout-orders.json");

function clean(value) {
  return String(value || "").trim();
}

export async function POST(request) {
  const body = await request.json().catch(() => null);

  if (!body) {
    return NextResponse.json({ error: "Invalid checkout details." }, { status: 400 });
  }

  const checkout = {
    product: clean(body.product),
    name: clean(body.name),
    email: clean(body.email),
    contactNumber: clean(body.contactNumber),
    amount: clean(body.amount),
    companyName: clean(body.companyName),
    address: clean(body.address),
    city: clean(body.city),
    state: clean(body.state),
    pinCode: clean(body.pinCode),
    gstNumber: clean(body.gstNumber),
    notes: clean(body.notes),
  };

  const requiredFields = ["product", "name", "email", "contactNumber", "amount", "address", "city", "state", "pinCode"];
  const missingField = requiredFields.find((field) => !checkout[field]);

  if (missingField) {
    return NextResponse.json({ error: "Please complete all required fields." }, { status: 400 });
  }

  if (!checkoutOptions.includes(checkout.product)) {
    return NextResponse.json({ error: "Please select a valid product or service." }, { status: 400 });
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(checkout.email)) {
    return NextResponse.json({ error: "Please enter a valid email address." }, { status: 400 });
  }

  if (!/^\d+(\.\d{1,2})?$/.test(checkout.amount)) {
    return NextResponse.json({ error: "Please enter a valid amount." }, { status: 400 });
  }

  await fs.mkdir(path.dirname(storageFile), { recursive: true });

  let existing = [];
  try {
    existing = JSON.parse(await fs.readFile(storageFile, "utf8"));
    if (!Array.isArray(existing)) {
      existing = [];
    }
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }

  existing.push({
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    ...checkout,
  });

  await fs.writeFile(storageFile, JSON.stringify(existing, null, 2));

  return NextResponse.json({ ok: true });
}
