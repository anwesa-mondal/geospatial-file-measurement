import React, { useState, Fragment } from 'react'
import { ChevronDown, ChevronRight, ChevronLeft, RefreshCw } from 'lucide-react'
import type { PaginatedMeasurementsResponse } from '../types'
import { FeaturePropertiesTable } from './FeaturePropertiesTable'
import { formatMetric } from '../lib/formatters'

interface MeasurementsTableProps {
  measurements: PaginatedMeasurementsResponse | null
  loading: boolean
  currentPage: number
  onPageChange: (newPage: number) => void
}

export const MeasurementsTable: React.FC<MeasurementsTableProps> = ({
  measurements,
  loading,
  currentPage,
  onPageChange,
}) => {
  // Set of expanded feature indexes
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set())

  const toggleRow = (index: number) => {
    setExpandedIndices((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  return (
    <div className="bg-white border border-zinc-200 rounded">
      {/* Header & Pagination */}
      <div className="p-3 border-b border-zinc-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-zinc-900">Computed Measurements</h3>
          <p className="text-xs text-zinc-500">
            {measurements
              ? `Showing ${measurements.items.length} of ${measurements.total} features (Click any row to expand/collapse properties)`
              : 'Loading...'}
          </p>
        </div>

        {measurements && measurements.pages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(Math.max(currentPage - 1, 1))}
              disabled={currentPage <= 1 || loading}
              className="p-1 border border-zinc-200 rounded hover:bg-zinc-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              title="Previous page"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="text-xs text-zinc-600">
              Page {measurements.page} of {measurements.pages}
            </span>
            <button
              onClick={() => onPageChange(Math.min(currentPage + 1, measurements.pages))}
              disabled={currentPage >= measurements.pages || loading}
              className="p-1 border border-zinc-200 rounded hover:bg-zinc-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              title="Next page"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Main Measurements Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-200 text-zinc-600 font-medium">
              <th className="py-2.5 px-3 w-8"></th>
              <th className="py-2.5 px-3 w-12">#</th>
              <th className="py-2.5 px-3">Geometry</th>
              <th className="py-2.5 px-3">Validation Status</th>
              <th className="py-2.5 px-3 text-right">Area (m²)</th>
              <th className="py-2.5 px-3 text-right">Perimeter (m)</th>
              <th className="py-2.5 px-3 text-right">Length (m)</th>
              <th className="py-2.5 px-3">Method</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 text-zinc-800 font-mono">
            {loading ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-zinc-500 font-sans">
                  <RefreshCw className="w-4 h-4 animate-spin inline mr-1 text-zinc-600" />
                  Loading feature measurements...
                </td>
              </tr>
            ) : measurements && measurements.items.length > 0 ? (
              measurements.items.map((feat) => {
                const isExpanded = expandedIndices.has(feat.feature_index)
                const isValid = feat.validation_status.toUpperCase() === 'VALID'

                return (
                  <Fragment key={feat.feature_index}>
                    {/* Clickable Feature Row */}
                    <tr
                      onClick={() => toggleRow(feat.feature_index)}
                      className={`cursor-pointer transition-colors ${
                        isExpanded ? 'bg-zinc-100/70 font-semibold' : 'hover:bg-zinc-50'
                      }`}
                    >
                      <td className="py-2.5 px-3 text-zinc-400">
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 text-zinc-700" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-zinc-500">{feat.feature_index}</td>
                      <td className="py-2.5 px-3 font-sans font-medium text-zinc-900">
                        {feat.geometry_type || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[11px] font-medium border ${
                            isValid
                              ? 'bg-zinc-100 text-zinc-800 border-zinc-300'
                              : 'bg-red-50 text-red-700 border-red-200'
                          }`}
                        >
                          {feat.validation_status}
                        </span>
                        {feat.validation_message && (
                          <div className="text-[10px] text-red-600 mt-1 font-mono">
                            {feat.validation_message}
                          </div>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right">{formatMetric(feat.area_sq_m)}</td>
                      <td className="py-2.5 px-3 text-right">{formatMetric(feat.perimeter_m)}</td>
                      <td className="py-2.5 px-3 text-right">{formatMetric(feat.length_m)}</td>
                      <td className="py-2.5 px-3 text-zinc-600 text-[11px]">
                        {feat.measurement_method || 'NONE'}
                      </td>
                    </tr>

                    {/* Expandable full-width row with fixed 5-row height & scroll */}
                    {isExpanded && (
                      <tr className="bg-zinc-50/50">
                        <td colSpan={8} className="p-3 border-t border-b border-zinc-200">
                          <FeaturePropertiesTable
                            properties={feat.properties}
                            featureIndex={feat.feature_index}
                          />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })
            ) : (
              <tr>
                <td colSpan={8} className="py-6 text-center text-zinc-500 font-sans">
                  No features found for this dataset.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
