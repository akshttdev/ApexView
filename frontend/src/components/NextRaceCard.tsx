'use client';

import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function NextRaceCard() {
  // Static fallback data
  const race = {
    name: 'Belgian Grand Prix',
    location: 'Spa-Francorchamps',
    date: 'July 28, 2024',
    countdown: '17d 05h 42m',
  };

  return (
    <Card className="bg-background text-foreground relative overflow-hidden flex flex-col sm:flex-row h-[180px]">
      <div className="flex-1 p-4">
        <CardHeader className="p-0 mb-2">
          <CardTitle>Next Race</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <p className="text-lg font-semibold">{race.name}</p>
          <p className="text-sm text-muted-foreground">{race.location} · {race.date}</p>
          <p className="mt-2 text-sm text-green-500">Starts in: {race.countdown}</p>
        </CardContent>
      </div>

      <div className="relative px-2  bottom-6 w-60 h-32 sm:w-62 sm:h-36 mr-4 mt-2 sm:mt-4 rounded-xl overflow-hidden">
        <Image
          src="/2.jpg"
          alt="Next race"
          fill
          className="object-cover"
          priority
        />
      </div>
    </Card>
  );
}
