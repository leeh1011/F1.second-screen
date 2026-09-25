import { CarMarker } from "@/components/track/CarMarker";
import { getCircuitCoordinates } from "@/hooks/useLiveSession";
import type { OpenF1Driver } from "@/lib/api/openf1";
import type { CarPosition } from "@/types/live";

type TrackMapProps = {
  cars: CarPosition[];
  circuitName: string;
  driversMap?: Map<number, OpenF1Driver>;
  isUpcoming?: boolean;
};

export function TrackMap({ cars, circuitName, driversMap, isUpcoming }: TrackMapProps) {
  // Generate SVG path for the track
  const trackPathPoints: string[] = [];
  const steps = 120;
  for (let i = 0; i <= steps; i += 1) {
    const prog = i / steps;
    const { x, y } = getCircuitCoordinates(prog);
    const px = x * 1000;
    const py = y * 520;
    trackPathPoints.push(`${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`);
  }
  const trackD = trackPathPoints.join(" ") + " Z";

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
      {/* Header Info */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isUpcoming ? "bg-amber-400" : "bg-red-500"} animate-pulse`} />
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-300">
            2D TRACK MAP & CIRCUITS
          </h2>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-medium text-zinc-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> DRS Zone
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-500" /> Sectors
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative rounded-xl border border-white/5 bg-zinc-950/90 p-2 shadow-inner">
        <svg viewBox="0 0 1000 520" className="h-[320px] w-full select-none">
          <defs>
            <linearGradient id="trackGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#27272a" />
              <stop offset="100%" stopColor="#18181b" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Grid Pattern */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#27272a" strokeWidth="0.5" opacity="0.4" />
          </pattern>
          <rect width="1000" height="520" fill="url(#grid)" rx="12" />

          {/* Track Outer Asphalt Border */}
          <path
            d={trackD}
            fill="none"
            stroke="#18181b"
            strokeWidth="42"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Track Base Asphalt */}
          <path
            d={trackD}
            fill="none"
            stroke="#27272a"
            strokeWidth="32"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* DRS Zone Highlight */}
          <path
            d={trackD}
            fill="none"
            stroke="#10b981"
            strokeWidth="6"
            strokeDasharray="180 400"
            strokeDashoffset="50"
            opacity="0.85"
            filter="url(#glow)"
          />

          {/* Track Racing Line */}
          <path
            d={trackD}
            fill="none"
            stroke="#52525b"
            strokeWidth="2"
            strokeDasharray="8 8"
          />

          {/* Start / Finish Line */}
          <g transform="translate(820, 240)">
            <line x1="0" y1="-20" x2="0" y2="20" stroke="#ffffff" strokeWidth="4" />
            <text x="8" y="4" fill="#a1a1aa" fontSize="10" fontWeight="700">FINISH</text>
          </g>

          {/* Render All Car Markers */}
          {!isUpcoming &&
            cars.map((car, index) => {
              const openf1Driver = driversMap?.get(car.driverNumber);
              return (
                <CarMarker
                  key={car.driverNumber}
                  car={car}
                  index={index}
                  teamColour={openf1Driver?.team_colour}
                />
              );
            })}
        </svg>

        {/* Upcoming Overlay Badge */}
        {isUpcoming && (
          <div className="absolute inset-0 flex flex-col items-center justify-center rounded-xl bg-zinc-950/75 backdrop-blur-sm p-6 text-center">
            <div className="mb-2 text-3xl">🗓️</div>
            <h3 className="text-sm font-extrabold text-amber-400 uppercase tracking-wider">
              UPCOMING GRAND PRIX
            </h3>
            <p className="mt-1 text-xs text-zinc-400 max-w-xs">
              Live car markers and GPS positioning will activate when session telecast begins.
            </p>
          </div>
        )}

        {/* Circuit Label Overlay */}
        <div className="absolute bottom-4 left-4 rounded-lg border border-white/10 bg-zinc-900/90 px-3 py-1.5 backdrop-blur-sm">
          <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            LOCATION
          </p>
          <p className="text-xs font-semibold text-zinc-200">{circuitName}</p>
        </div>
      </div>
    </section>
  );
}


