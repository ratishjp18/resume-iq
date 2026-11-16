import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { STATUS_META } from '../utils/format'

const KEYS = ['matched', 'uncertain', 'not_evidenced']

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-white/15 bg-ink-800/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
      {label && <p className="mb-1 font-semibold text-white">{label}</p>}
      {payload.map((p) => (
        <p key={p.dataKey ?? p.name} className="flex items-center gap-2 text-slate-300">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color ?? p.payload?.fill }} />
          {p.name}: <span className="font-semibold text-white">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export function StatusDonut({ matched, uncertain, notEvidenced }) {
  const counts = { matched, uncertain, not_evidenced: notEvidenced }
  const total = matched + uncertain + notEvidenced
  const pct = total ? Math.round((matched / total) * 100) : 0
  const data = KEYS.map((k) => ({ key: k, name: STATUS_META[k].label, value: counts[k] })).filter((d) => d.value > 0)
  return (
    <div role="img" aria-label={`Requirement status: ${matched} matched, ${uncertain} uncertain, ${notEvidenced} not evidenced`}>
      <div className="relative" style={{ height: 230 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={72} outerRadius={104} paddingAngle={4} cornerRadius={8}
              stroke="none" startAngle={90} endAngle={-270} animationDuration={900}>
              {data.map((d) => <Cell key={d.key} fill={STATUS_META[d.key].color} />)}
            </Pie>
            <Tooltip content={<ChartTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="font-display text-4xl font-bold text-white">{pct}%</p>
            <p className="text-xs text-slate-400">of {total} requirements<br />matched</p>
          </div>
        </div>
      </div>
      <ul className="mt-3 grid grid-cols-3 gap-2 text-center">
        {KEYS.map((k) => (
          <li key={k} className="rounded-xl border border-white/10 bg-white/[0.03] px-2 py-2">
            <p className="font-display text-xl font-bold" style={{ color: STATUS_META[k].color }}>{counts[k]}</p>
            <p className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
              <span className="h-2 w-2 rounded-full" style={{ background: STATUS_META[k].color }} aria-hidden="true" />
              {STATUS_META[k].label}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CategoryBars({ rows }) {
  const sorted = [...rows].sort((a, b) => (b.matched + b.uncertain + b.not_evidenced) - (a.matched + a.uncertain + a.not_evidenced))
  return (
    <div role="img" aria-label="Requirements by category and status">
      <div style={{ height: Math.max(200, sorted.length * 46 + 20) }}>
        <ResponsiveContainer>
          <BarChart data={sorted} layout="vertical" margin={{ left: 4, right: 20, top: 4, bottom: 4 }} barSize={16}>
            <CartesianGrid stroke="rgba(255,255,255,.06)" strokeDasharray="3 5" horizontal={false} />
            <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="category" width={120} stroke="#cbd5e1" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,.05)', radius: 8 }} />
            <Bar dataKey="matched" name="Matched" stackId="a" fill={STATUS_META.matched.color} radius={[8, 0, 0, 8]} animationDuration={800} />
            <Bar dataKey="uncertain" name="Uncertain" stackId="a" fill={STATUS_META.uncertain.color} animationDuration={800} />
            <Bar dataKey="not_evidenced" name="Not evidenced" stackId="a" fill={STATUS_META.not_evidenced.color} radius={[0, 8, 8, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 flex flex-wrap justify-center gap-4 text-xs text-slate-400">
        {KEYS.map((k) => (
          <li key={k} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: STATUS_META[k].color }} aria-hidden="true" />{STATUS_META[k].label}
          </li>
        ))}
      </ul>
    </div>
  )
}
