"use client";

import { useEffect, useState } from "react";
import { Search, ChevronDown, ListFilter, LayoutGrid, List, Plus, MoreVertical, PauseCircle, CheckCircle2, Circle, Clock } from "lucide-react";

import { api } from "@/lib/api";
import type { AdminAnalytics, AdminToday, Conversation, Health, Reservation } from "@/types/api";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [today, setToday] = useState<AdminToday | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [errors, setErrors] = useState<number>(0);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    void Promise.all([
      api.analytics().then(setAnalytics),
      api.today().then(setToday),
      api.reservations().then(setReservations),
      api.conversations().then(setConversations),
      api.errors().then((value) => setErrors(value.length)),
      api.health().then(setHealth),
    ]);
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-normal text-foreground">Dashboard</h1>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search for a reservation"
              className="h-8 w-64 rounded-md border border-border bg-muted pl-8 pr-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary"
            />
          </div>
          <button className="flex h-8 items-center gap-2 rounded-md border border-border bg-muted px-3 text-xs font-medium text-muted-foreground hover:text-foreground">
            Status <ChevronDown className="h-3 w-3" />
          </button>
          <button className="flex h-8 items-center gap-2 rounded-md border border-border bg-muted px-3 text-xs font-medium text-muted-foreground hover:text-foreground">
            <ListFilter className="h-3 w-3" /> Sorted by time
          </button>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <button className="flex h-8 w-8 items-center justify-center rounded-md bg-[#2c2c2c] text-foreground">
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground">
              <List className="h-4 w-4" />
            </button>
          </div>
          <button className="flex h-8 items-center gap-1.5 rounded-md bg-emerald-600 px-3 text-xs font-medium text-card-foreground hover:bg-emerald-700">
            <Plus className="h-4 w-4" /> New reservation
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="grid gap-4 sm:grid-cols-2">
            {reservations.length === 0 ? (
              <div className="col-span-2 flex h-32 items-center justify-center rounded-lg border border-border border-dashed text-sm text-muted-foreground">
                No reservations found
              </div>
            ) : (
              reservations.slice(0, 6).map((item) => (
                <div key={item.id} className="rounded-lg border border-border bg-card p-5 hover:border-muted-foreground/50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-card-foreground">{item.customer_name ?? `Reservation #${item.id}`}</h3>
                      <p className="mt-1 text-xs text-muted-foreground">{item.people} guests | {item.reservation_time}</p>
                    </div>
                    <button className="text-muted-foreground hover:text-card-foreground">
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="mt-6 flex items-center gap-2">
                    {item.status === 'confirmed' ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <Clock className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-xs text-muted-foreground">Reservation is {item.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <div className="rounded-lg border border-border bg-card p-5">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h3 className="text-sm font-medium text-card-foreground">System Usage</h3>
                <p className="mt-1 text-xs text-muted-foreground">Current operational snapshot</p>
              </div>
              <button className="rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-500 hover:bg-emerald-500/20">
                Refresh Stats
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground">
                  <Circle className="h-3 w-3" />
                  <span>Today's Rsvps</span>
                </div>
                <div className="text-xs text-card-foreground">
                  {today?.reservations ?? "—"} <span className="text-muted-foreground">/ 100</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground">
                  <Circle className="h-3 w-3" />
                  <span>Total Customers</span>
                </div>
                <div className="text-xs text-card-foreground">
                  {analytics?.customers ?? "—"} <span className="text-muted-foreground">/ 1,000</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground">
                  <Circle className="h-3 w-3" />
                  <span>Conversations</span>
                </div>
                <div className="text-xs text-card-foreground">
                  {conversations.length} <span className="text-muted-foreground">/ 500</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground">
                  <Circle className="h-3 w-3" />
                  <span>System Errors</span>
                </div>
                <div className="text-xs text-card-foreground">
                  {errors} <span className="text-muted-foreground">/ 50</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground">
                  <Circle className="h-3 w-3" />
                  <span>Backend Health</span>
                </div>
                <div className="text-xs text-emerald-500">
                  {health ? "Online" : "Checking"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
