"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarCheck2, Check, Clock3, Hotel, Phone, Search, Users, X } from "lucide-react";

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
const reservationTypes = ["hotel", "restaurant", "clinic", "beauty", "wellness", "automotive", "meeting_room", "generic"];

const initialForm = {
  customer_name: "",
  phone: "",
  email: "",
  reservation_date: "",
  reservation_time: "",
  people: 2,
  type: "hotel",
  room_type: "",
  nights: "",
  service: "",
  notes: "",
};

function parseNotes(notes?: string | null) {
  const data: Record<string, string> = {};
  const text: string[] = [];
  for (const part of (notes ?? "").split("|").map((item) => item.trim()).filter(Boolean)) {
    const match = part.match(/^([a-z_]+)=(.+)$/i);
    if (match) data[match[1]] = match[2];
    else text.push(part);
  }
  return {
    type: data.type ?? "generic",
    roomType: data.room_type ?? "",
    service: data.service ?? "",
    nights: data.nights ?? "",
    checkoutDate: data.checkout_date ?? "",
    text: text.join(" | "),
  };
}

function label(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusClass(status: string) {
  if (status === "confirmed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (status === "pending") return "border-amber-200 bg-amber-50 text-amber-700";
  if (status === "cancelled") return "border-red-200 bg-red-50 text-red-700";
  return "bg-muted text-muted-foreground";
}

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [query, setQuery] = useState("");
  const [date, setDate] = useState("");
  const [status, setStatus] = useState("all");
  const [type, setType] = useState("all");
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    void api.reservations().then(setReservations).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const today = new Date().toISOString().slice(0, 10);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return reservations.filter((item) => {
      const details = parseNotes(item.notes);
      const haystack = [item.customer_name, item.phone, item.email, item.status, item.notes, details.type].join(" ").toLowerCase();
      if (date && item.reservation_date !== date) return false;
      if (status !== "all" && item.status !== status) return false;
      if (type !== "all" && details.type !== type) return false;
      if (needle && !haystack.includes(needle)) return false;
      return true;
    });
  }, [date, query, reservations, status, type]);

  const todayReservations = reservations.filter((item) => item.reservation_date === today && item.status !== "cancelled");

  async function createReservation() {
    setSaving(true);
    const notes = [
      `type=${form.type}`,
      form.room_type ? `room_type=${form.room_type}` : "",
      form.nights ? `nights=${form.nights}` : "",
      form.service ? `service=${form.service}` : "",
      form.notes,
    ].filter(Boolean).join(" | ");
    await api.createReservation({
      customer_name: form.customer_name,
      phone: form.phone,
      email: form.email,
      reservation_date: form.reservation_date,
      reservation_time: form.reservation_time,
      people: form.people,
      notes,
    });
    setForm(initialForm);
    setSaving(false);
    load();
  }

  async function updateStatus(id: number, nextStatus: string) {
    await api.updateReservation(id, { status: nextStatus });
    load();
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Reservations</h1>
          <p className="text-sm text-muted-foreground">Track real bookings created by live agents and staff.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>Refresh</Button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Total records" value={reservations.length} icon={CalendarCheck2} />
        <Metric label="Today" value={todayReservations.length} icon={Clock3} />
        <Metric label="Guests today" value={todayReservations.reduce((sum, item) => sum + item.people, 0)} icon={Users} />
        <Metric label="Confirmed" value={reservations.filter((item) => item.status === "confirmed").length} icon={Check} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader><CardTitle>New Record</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })}>
              {reservationTypes.map((item) => <option key={item} value={item}>{label(item)}</option>)}
            </Select>
            <Input placeholder="Customer name" value={form.customer_name} onChange={(event) => setForm({ ...form, customer_name: event.target.value })} />
            <Input placeholder="Phone" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            <Input placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <Input type="date" value={form.reservation_date} onChange={(event) => setForm({ ...form, reservation_date: event.target.value })} />
              <Input type="time" value={form.reservation_time} onChange={(event) => setForm({ ...form, reservation_time: event.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Input type="number" min={1} value={form.people} onChange={(event) => setForm({ ...form, people: Number(event.target.value) })} />
              <Input placeholder="Nights" value={form.nights} onChange={(event) => setForm({ ...form, nights: event.target.value })} />
            </div>
            <Input placeholder="Room type or service" value={form.type === "hotel" ? form.room_type : form.service} onChange={(event) => {
              const value = event.target.value;
              setForm(form.type === "hotel" ? { ...form, room_type: value } : { ...form, service: value });
            }} />
            <Textarea placeholder="Internal notes" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
            <Button className="w-full" onClick={createReservation} disabled={saving || !form.customer_name || !form.reservation_date || !form.reservation_time}>
              {saving ? "Saving" : "Create record"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <CardTitle>Reservation Records</CardTitle>
                <Badge>{filtered.length} shown</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-[1fr_150px_150px_150px]">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input className="pl-9" placeholder="Search name, phone, notes" value={query} onChange={(event) => setQuery(event.target.value)} />
                </div>
                <Input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
                <Select value={type} onChange={(event) => setType(event.target.value)}>
                  <option value="all">All types</option>
                  {reservationTypes.map((item) => <option key={item} value={item}>{label(item)}</option>)}
                </Select>
                <Select value={status} onChange={(event) => setStatus(event.target.value)}>
                  {statuses.map((item) => <option key={item} value={item}>{label(item)}</option>)}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {filtered.length === 0 ? (
              <EmptyState title={loading ? "Loading reservations" : "No reservations match the filters"} />
            ) : filtered.map((item) => <ReservationRow key={item.id} item={item} onStatus={updateStatus} />)}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: number; icon: typeof CalendarCheck2 }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary"><Icon className="h-5 w-5" /></div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </div>
    </div>
  );
}

function ReservationRow({ item, onStatus }: { item: Reservation; onStatus: (id: number, status: string) => Promise<void> }) {
  const details = parseNotes(item.notes);
  const primaryDetail = details.type === "hotel" && details.roomType ? `${details.roomType} room` : details.service || label(details.type);
  return (
    <div className="grid gap-3 rounded-md border bg-background p-3 text-sm lg:grid-cols-[minmax(0,1fr)_auto]">
      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">{item.customer_name ?? `Reservation #${item.id}`}</p>
          <Badge className={statusClass(item.status)}>{label(item.status)}</Badge>
          <Badge>{label(details.type)}</Badge>
        </div>
        <div className="grid gap-2 text-muted-foreground md:grid-cols-3">
          <span>{item.reservation_date} {item.reservation_time.slice(0, 5)}</span>
          <span>{item.people} guests</span>
          {item.phone ? <span className="inline-flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" />{item.phone}</span> : <span />}
        </div>
        <div className="flex flex-wrap gap-2">
          {primaryDetail ? <Badge className="border-blue-200 bg-blue-50 text-blue-700"><Hotel className="mr-1 h-3 w-3" />{primaryDetail}</Badge> : null}
          {details.nights ? <Badge>{details.nights} nights</Badge> : null}
          {details.checkoutDate ? <Badge>Checkout {details.checkoutDate}</Badge> : null}
        </div>
        {details.text ? <p className="line-clamp-2 text-muted-foreground">{details.text}</p> : null}
      </div>
      <div className="flex items-center gap-2 lg:justify-end">
        <Button variant="outline" size="sm" onClick={() => void onStatus(item.id, "confirmed")} disabled={item.status === "confirmed"}>
          <Check className="h-4 w-4" /> Confirm
        </Button>
        <Button variant="destructive" size="sm" onClick={() => void onStatus(item.id, "cancelled")} disabled={item.status === "cancelled"}>
          <X className="h-4 w-4" /> Cancel
        </Button>
      </div>
    </div>
  );
}
