import { Badge } from "@/components/ui/badge";

interface Tier {
  name: string;
  pointsNeeded: number;
  perks: string[];
}

interface Props {
  currentPoints: number;
}

const TIERS: Tier[] = [
  { name: 'Watch Pal', pointsNeeded: 0, perks: ['Basic chat'] },
  { name: 'Super Buddy', pointsNeeded: 50, perks: ['Custom emojis', 'Party invites'] },
  { name: 'Epic Watch Buddies', pointsNeeded: 120, perks: ['Special reel effects', 'Priority invites'] },
  { name: 'Legendary Binge Duo', pointsNeeded: 250, perks: ['Exclusive themes', 'VIP watch rooms'] },
];

export default function TiersView({ currentPoints }: Props) {
  // Find current tier
  const currentTierIndex = TIERS.reduce((idx, tier, i) => (currentPoints >= tier.pointsNeeded ? i : idx), 0);
  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="text-center text-white text-lg">Watch Buddy Points: <span className="font-bold">{currentPoints}</span></div>
      {TIERS.map((tier, idx) => {
        const reached = currentPoints >= tier.pointsNeeded;
        return (
          <div key={tier.name} className={`p-4 rounded-xl ${reached ? 'bg-green-700/60' : 'bg-white/5'} flex flex-col gap-2`}>
            <div className="flex items-center gap-2">
              <div className="text-xl font-semibold text-white">{tier.name}</div>
              {idx === currentTierIndex && <Badge variant="secondary">Current</Badge>}
            </div>
            <div className="text-sm text-gray-300">Requires {tier.pointsNeeded} points</div>
            <ul className="list-disc list-inside text-gray-300 text-sm">
              {tier.perks.map((perk) => (
                <li key={perk}>{perk}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
} 