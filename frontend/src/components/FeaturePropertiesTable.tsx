import React from 'react'

interface FeaturePropertiesTableProps {
  properties: Record<string, any> | null
  featureIndex: number
}

export const FeaturePropertiesTable: React.FC<FeaturePropertiesTableProps> = ({
  properties,
  featureIndex,
}) => {
  if (!properties || Object.keys(properties).length === 0) {
    return (
      <div className="py-3 px-4 text-xs text-zinc-500 italic bg-zinc-50 border border-zinc-200 rounded">
        Feature #{featureIndex} has no source properties or attributes.
      </div>
    )
  }

  const entries = Object.entries(properties)

  return (
    <div className="w-full bg-zinc-50/80 border border-zinc-200 rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-semibold text-zinc-700 uppercase tracking-wider">
          Feature #{featureIndex} Properties ({entries.length} attributes)
        </span>
        <span className="text-[11px] text-zinc-400">
          Showing scrollable attribute list
        </span>
      </div>

      {/* Fixed height of ~5 rows (~180px) with vertical scroll */}
      <div className="overflow-y-auto max-h-[180px] border border-zinc-200 rounded bg-white shadow-xs">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 bg-zinc-100 border-b border-zinc-200 z-10">
            <tr className="text-zinc-700 font-medium">
              <th className="py-1.5 px-3 w-1/3 border-r border-zinc-200">Property Key</th>
              <th className="py-1.5 px-3">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 font-mono text-[11px]">
            {entries.map(([key, value]) => {
              const displayValue =
                value === null || value === undefined
                  ? 'null'
                  : typeof value === 'object'
                  ? JSON.stringify(value, null, 2)
                  : String(value)

              return (
                <tr key={key} className="hover:bg-zinc-50 transition-colors">
                  <td className="py-1.5 px-3 text-zinc-900 font-medium border-r border-zinc-200 break-all select-text">
                    {key}
                  </td>
                  <td className="py-1.5 px-3 text-zinc-600 break-all font-sans select-text whitespace-pre-wrap">
                    {displayValue}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
