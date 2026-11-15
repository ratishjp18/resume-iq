import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { STATUS_META } from '../utils/format'

const tip = { background: '#111833', border: '1px solid rgba(255,255,255,.15)', borderRadius: 12, color: '#e2e8f0' }

export function StatusDonut({ matched, uncertain, notEvidenced }) {
  const data = [
    { key: 'matched', name: 'Matched', value: matched },
    { key: 'uncertain', name: 'Uncertain', value: uncertain },
    { key: 'not_evidenced', name: 'Not evidenced', value: notEvidenced },
  ].filter((d) => d.value > 0)
  return (
    <div style={{ height: 260 }} role="img" aria-label={`Requirement status: ${matched} matched, ${uncertain} uncertain, ${notEvidenced} not evidenced`}>
      <ResponsiveContainer>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3} stroke="none">
            {data.map((d) => <Cell key={d.key} fill={STATUS_META[d.key].color} />)}
          </Pie>
          <Tooltip contentStyle={tip} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CategoryBars({ rows }) {
  return (
    <div style={{ height: Math.max(220, rows.length * 44 + 60) }} role="img" aria-label="Requirements by category and status">
      <ResponsiveContainer>
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid stroke="rgba(255,255,255,.06)" horizontal={false} />
          <XAxis type="number" allowDecimals={false} stroke="#94a3b8" fontSize={12} />
          <YAxis type="category" dataKey="category" width={130} stroke="#94a3b8" fontSize={12} />
          <Tooltip contentStyle={tip} cursor={{ fill: 'rgba(255,255,255,.04)' }} />
          <Legend />
          <Bar dataKey="matched" name="Matched" stackId="a" fill={STATUS_META.matched.color} />
          <Bar dataKey="uncertain" name="Uncertain" stackId="a" fill={STATUS_META.uncertain.color} />
          <Bar dataKey="not_evidenced" name="Not evidenced" stackId="a" fill={STATUS_META.not_evidenced.color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
