'use client';

import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEffect, useState } from 'react';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

interface FastestLapData {
  driver_name: string;
  abbreviation: string;
  team: string;
  lap_time: string;
  race_name: string;
  date: string;
  sector_times: number[];
}

export default function FastestLapChart() {
  const [data, setData] = useState<FastestLapData[]>([]);

  useEffect(() => {
    // Sample static data
    const staticData: FastestLapData[] = [
      {
        driver_name: 'Oliver Bearman',
        abbreviation: 'BEA',
        team: 'Haas',
        lap_time: '1:19.321',
        race_name: 'British Grand Prix',
        date: '2024-07-07',
        sector_times: [24.1, 32.5, 22.7],
      },
      {
        driver_name: 'Max Verstappen',
        abbreviation: 'VER',
        team: 'Red Bull Racing',
        lap_time: '1:19.561',
        race_name: 'British Grand Prix',
        date: '2024-07-07',
        sector_times: [24.3, 32.7, 22.6],
      },
      {
        driver_name: 'Lando Norris',
        abbreviation: 'NOR',
        team: 'McLaren',
        lap_time: '1:19.782',
        race_name: 'British Grand Prix',
        date: '2024-07-07',
        sector_times: [24.5, 32.8, 22.8],
      },
    ];

    setData(staticData);
  }, []);

  const createChartData = (driver: FastestLapData) => ({
    labels: ['Sector 1', 'Sector 2', 'Sector 3'],
    datasets: [
      {
        label: `${driver.lap_time}`, // Label used in tooltip only
        data: driver.sector_times,
        fill: true,
        backgroundColor: 'rgba(255,255,255,0.05)',
        borderColor: '#aaa',
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#fff',
        pointHoverRadius: 6,
      },
    ],
  });

  const chartOptions = (lapTime: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${ctx.parsed.y.toFixed(3)}s`,
        },
      },
      customTextOverlay: {
        lapTime,
      },
    },
    scales: {
      x: {
        ticks: { color: '#aaa' },
        grid: { display: false },
      },
      y: {
        ticks: { color: '#fff' },
        grid: { display: false },
      },
    },
  });

  // Plugin to render lap time text inside chart
  ChartJS.register({
    id: 'customTextOverlay',
    beforeDraw: (chart, args, options: any) => {
      const { ctx, chartArea } = chart;
      const { left, right, top, bottom, width } = chartArea;
      ctx.save();
      ctx.font = 'bold 12px sans-serif';
      ctx.fillStyle = '#aaa';
      ctx.textAlign = 'right';
      ctx.fillText(`Lap: ${options.lapTime}`,  (left+width/2) + 35, bottom - 10);
      ctx.restore();
    },
  });

  return (
    <Card className="bg-transparent border border-zinc-800">
      <CardHeader>
        <CardTitle className="text-white text-lg">Fastest Lap Sectors</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.map((driver, idx) => (
            <Card key={idx} className="bg-transparent border border-zinc-700">
              <CardContent className="flex flex-col items-center pt-4">
                <p className="text-white text-sm mb-1">{driver.driver_name}</p>
                <p className="text-zinc-400 text-xs mb-2">{driver.team}</p>
                <div className="h-[200px] w-full">
                  <Line
                    data={createChartData(driver)}
                    options={chartOptions(driver.lap_time)}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
