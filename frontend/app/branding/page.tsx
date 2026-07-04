"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { BrandProfile } from "@/types/api";

export default function BrandingPage() {
  const [brand, setBrand] = useState<BrandProfile | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => { void api.branding().then(setBrand); }, []);
  async function save() {
    if (!brand) return;
    const updated = await api.updateBranding(brand);
    setBrand(updated);
    setMessage("Brand profile saved.");
  }
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Branding</h1><p className="text-sm text-muted-foreground">White-label brand kit for business-facing experiences.</p></div>
      {brand ? (
        <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
          <Card><CardHeader><CardTitle>Brand Profile</CardTitle></CardHeader><CardContent className="space-y-3">
            <Input value={brand.name} onChange={(e) => setBrand({ ...brand, name: e.target.value })} />
            <Input placeholder="Logo URL" value={brand.logo_url ?? ""} onChange={(e) => setBrand({ ...brand, logo_url: e.target.value })} />
            <Input type="color" value={brand.primary_color} onChange={(e) => setBrand({ ...brand, primary_color: e.target.value })} />
            <Input type="color" value={brand.accent_color} onChange={(e) => setBrand({ ...brand, accent_color: e.target.value })} />
            <Input placeholder="Support email" value={brand.support_email ?? ""} onChange={(e) => setBrand({ ...brand, support_email: e.target.value })} />
            <Input placeholder="Custom domain" value={brand.custom_domain ?? ""} onChange={(e) => setBrand({ ...brand, custom_domain: e.target.value })} />
            <Button onClick={save}>Save Brand</Button>
            {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
          </CardContent></Card>
          <Card><CardHeader><CardTitle>Preview</CardTitle></CardHeader><CardContent>
            <div className="rounded-lg border p-6" style={{ borderColor: brand.primary_color }}>
              <div className="mb-4 h-10 w-10 rounded-md" style={{ backgroundColor: brand.primary_color }} />
              <h2 className="text-xl font-semibold">{brand.name}</h2>
              <p className="text-sm text-muted-foreground">AI assistant powered by your local white-label platform.</p>
              <button className="mt-4 rounded-md px-3 py-2 text-sm text-white" style={{ backgroundColor: brand.accent_color }}>Start Conversation</button>
            </div>
          </CardContent></Card>
        </div>
      ) : null}
    </div>
  );
}
