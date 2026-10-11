import React from 'react'
import { Database, RefreshCw, Clock } from 'lucide-react'
import type { FileResponse } from '../types'

interface FileLookupCardProps {
  fileIdInput: string
  activeFile: FileResponse | null
  polling: boolean
  onFileIdChange: (val: string) => void
  onLookup: (id: string) => void
}

export const FileLookupCard: React.FC<FileLookupCardProps> = ({
  fileIdInput,
  activeFile,
  polling,
  onFileIdChange,
  onLookup,
}) => {
  return (
    <div className="bg-white border border-zinc-200 rounded p-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Database className="w-4 h-4 text-zinc-600" />
          <h2 className="text-sm font-semibold text-zinc-800 uppercase tracking-wide">
            Lookup Existing File
          </h2>
        </div>
        <p className="text-xs text-zinc-500 mb-3">
          Query processing state and persisted measurements for an existing UUID.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              File ID (UUID)
            </label>
            <input
              type="text"
              value={fileIdInput}
              onChange={(e) => onFileIdChange(e.target.value)}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              className="w-full text-xs border border-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-500 font-mono"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onLookup(fileIdInput)}
              disabled={!fileIdInput.trim()}
              className="flex-1 text-xs font-medium py-2 px-3 border border-zinc-300 bg-white text-zinc-800 rounded hover:bg-zinc-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Fetch Status
            </button>
            {activeFile && (
              <button
                type="button"
                onClick={() => onLookup(activeFile.id)}
                className="text-xs font-medium py-2 px-3 border border-zinc-200 bg-zinc-50 text-zinc-600 rounded hover:bg-zinc-100 flex items-center gap-1 cursor-pointer"
                title="Refresh current file"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${polling ? 'animate-spin text-zinc-800' : ''}`} />
                Refresh
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="text-[11px] text-zinc-400 mt-4 border-t border-zinc-100 pt-2 flex items-center gap-1">
        <Clock className="w-3 h-3" />
        <span>Background tasks consumed asynchronously via Redis Streams</span>
      </div>
    </div>
  )
}
