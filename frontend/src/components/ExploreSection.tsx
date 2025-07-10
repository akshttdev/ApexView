// components/ExploreSection.tsx
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const sections = [
  { title: "Telemetry Analysis", href: "/telemetry", icon: "" },
  { title: "Track Map", href: "/track-map", icon: "" },
  { title: "Strategy Simulator", href: "/strategy", icon: "" },
  { title: "Standings", href: "/standings", icon: "" },
];

export default function ExploreSection() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4 text-white">Explore</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {sections.map(({ title, href, icon }) => (
          <Link key={title} href={href}>
            <Card className="bg-transparent hover:bg-zinc-800 transition duration-200 cursor-pointer aspect-square flex items-center justify-center">
              <CardContent className="flex flex-col items-center justify-center space-y-2">
                <span className="text-3xl">{icon}</span>
                <CardTitle className="text-sm font-medium text-white text-center">{title}</CardTitle>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
