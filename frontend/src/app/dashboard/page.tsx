// app/dashboard/page.tsx
'use client';

import Image from 'next/image';
import NextRaceCard from "@/components/NextRaceCard";
import TopDrivers from "@/components/TopDrivers";
import FastestLapChart from "@/components/FastestLapChart";
import ExploreSection from "@/components/ExploreSection";

export default function DashboardPage() {
  return (
    <section className="px-6 py-6 space-y-10">
      <h1 className="text-6xl font-bold text-center">Dashboard</h1>

      {/* Full-width banner image with overlay text */}
      <div className="relative w-full h-78 rounded-xl overflow-hidden">
        <Image
          src="/3.jpg"
          alt="Banner"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
          <h2 className="text-white text-4xl font-bold">ApexView </h2>
        </div>
      </div>

      {/* Main content cards */}
      <NextRaceCard />
      <TopDrivers />
      <FastestLapChart />
      <ExploreSection />
    </section>
  );
}
