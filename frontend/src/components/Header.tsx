import React from 'react'
import { Layers, ExternalLink } from 'lucide-react'

export const Header: React.FC = () => {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-zinc-700" />
          <span className="font-semibold text-base text-zinc-900 tracking-tight">
            Geospatial Measurement Console
          </span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-zinc-500 hover:text-zinc-800 flex items-center gap-1 border border-zinc-200 px-2.5 py-1 rounded bg-zinc-50 hover:bg-zinc-100 transition-colors"
          >
            Swagger Docs
            <ExternalLink className="w-3 h-3" />
          </a>
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            FastAPI :8000
          </span>
        </div>
      </div>
    </header>
  )
}
