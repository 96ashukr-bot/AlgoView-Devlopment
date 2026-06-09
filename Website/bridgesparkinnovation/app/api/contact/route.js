import fs from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";
import { serviceOptions } from "@/lib/site";

const storageFile = path.join(process.cwd(), "storage", "enquiries.json");

function clean(value) {
  return String(value || "").trim();
}

export async function POST(request) {
  const body = await request.json().catch(() => null);

  if (!body) {
    return NextResponse.json({ error: "Invalid enquiry details." }, { status: 400 });
  }

  const enquiry = {
    name: clean(body.name),
    mobile: clean(body.mobile),
    email: clean(body.email),
    service: clean(body.service),
    message: clean(body.message),
  };

  if (!enquiry.name || !enquiry.mobile || !enquiry.email || !enquiry.service || !enquiry.message) {
    return NextResponse.json({ error: "All fields are required." }, { status: 400 });
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(enquiry.email)) {
    return NextResponse.json({ error: "Please enter a valid email address." }, { status: 400 });
  }

  if (!serviceOptions.includes(enquiry.service)) {
    return NextResponse.json({ error: "Please select a valid service." }, { status: 400 });
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
    ...enquiry,
  });

  await fs.writeFile(storageFile, JSON.stringify(existing, null, 2));

  return NextResponse.json({ ok: true });
}
