"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Reservation } from "@/types/api";

const statuses = ["all", "pending", "confirmed", "cancelled", "completed", "no_show"];

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [date, setDate] = useState("");
  const [status, setStatus] = useState("all");
  const [form, setForm] = useState({ customer_name: "", phone: "", reservation_date: "", reservation_time: "", people: 2, notes: "" });

  const load = () => void api.reservations().then(setReservations);
  useEffect(load, []);

  const filtered = useMemo(() => reservations.filter((item) => {
    if (date && item.reservation_date !== date) return false;
    if (status !== "all" && item.status !== status) return false;
    return true;
  }), [date, reservations, status]);

  async function createReservation() {
    await api.createReservation(form);
    setForm({ customer_name: "", phone: "", reservation_date: "", reservation_time: "", people: 2, notes: "" });
    load();
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Reservations</h1>
        <p className="text-sm text-muted-foreground">Create, update, cancel and filter live reservations.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[380px_1fr]">
        <Card>
          <CardHeader><CardTitle>Create Reservation</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Customer name" value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
            <Input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <Input type="date" value={form.reservation_date} onChange={(e) => setForm({ ...form, reservation_date: e.target.value })} />
              <Input type="time" value={form.reservation_time} onChange={(e) => setForm({ ...form, reservation_time: e.target.value })} />
            </div>
            <Input type="number" min={1} value={form.people} onChange={(e) => setForm({ ...form, people: Number(e.target.value) })} />
            <Textarea placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            <Button onClick={createReservation} disabled={!form.customer_name || !form.reservation_date || !form.reservation_time}>Create</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <CardTitle>Reservation List</CardTitle>
              <div className="flex gap-2">
                <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                <Select value={status} onChange={(e) => setStatus(e.target.value)}>{statuses.map((item) => <option key={item}>{item}</option>)}</Select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {filtered.length === 0 ? <EmptyState title="No reservations match the filters" /> : filtered.map((item) => (
              <div key={item.id} className="grid gap-3 rounded-md border p-3 text-sm md:grid-cols-[1fr_auto]">
                <div>
                  <div className="flex items-center gap-2"><p className="font-medium">{item.customer_name ?? `Reservation #${item.id}`}</p><Badge>{item.status}</Badge></div>
                  <p className="text-muted-foreground">{item.reservation_date} {item.reservation_time} · {item.people} guests</p>
                  {item.notes ? <p className="mt-1 text-muted-foreground">{item.notes}</p> : null}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => void api.updateReservation(item.id, { status: "confirmed" }).then(load)}>Confirm</Button>
                  <Button variant="destructive" size="sm" onClick={() => void api.cancelReservation(item.id).then(load)}>Cancel</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
