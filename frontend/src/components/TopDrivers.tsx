'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { useEffect, useState } from 'react';

interface Driver {
  name: string;
  team: string;
  points: number;
}

export default function TopDrivers() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
  const fetchDrivers = async () => {
    try {
      const res = await fetch('http://localhost:8000/drivers');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();

      const formatted = data.map((d: any) => ({
        name: d.driver_name,      // <-- mapping it
        team: d.team,
        points: d.points,
      }));

      const top10 = formatted
        .sort((a: Driver, b: Driver) => b.points - a.points)
        .slice(0, 10);

      setDrivers(top10);
    } catch (err) {
      console.error('Error fetching top drivers:', err);
      setError('Failed to load drivers');
    } finally {
      setLoading(false);
    }
  };

  fetchDrivers();
}, []);


  return (
    <div className="w-full space-y-2">
      {/* Title outside card */}
      
      {/* Card */}
      <Card className="bg-transparent border border-zinc-800 w-full">
        <h2 className="text-white text-lg font-semibold  px-4"> Top 10 Drivers</h2>

        <CardHeader />

        <CardContent className="space-y-3">
          {/* Key Row */}
          <div className="grid grid-cols-[40px_1fr_1fr_80px] text-sm font-semibold text-zinc-400 border-b border-zinc-700 pb-1">
            <span>Pos</span>
            <span>Name</span>
            <span>Team</span>
            <span className="text-right">Points</span>
          </div>

          {/* Driver Rows */}
          {loading ? (
            <div className="text-zinc-400 text-center py-8">Loading drivers...</div>
          ) : error ? (
            <div className="text-red-500 text-center py-8">{error}</div>
          ) : (
            <ul className="space-y-2">
              {drivers.map((d, i) => (
                <li
                  key={i}
                  className="grid grid-cols-[40px_1fr_1fr_80px] text-sm text-white border-b border-zinc-800 pb-1 items-center"
                >
                  <span className="font-bold">{i + 1}</span>
                  <span className="truncate">{d.name}</span>
                  <span className="text-zinc-400 truncate">{d.team}</span>
                  <span className="font-semibold text-green-400 text-right">{d.points} pts</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
