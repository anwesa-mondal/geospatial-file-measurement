import React from 'react'
import { FileCheck } from 'lucide-react'
import type { FileResponse } from '../types'
import { formatBytes } from '../lib/formatters'

interface FileMetadataCardProps {
  file: FileResponse
}

export const FileMetadataCard: React.FC<FileMetadataCardProps> = ({ file }) => {
  const isCompleted = file.status.toLowerCase() === 'completed'
  const isProcessing = file.status.toLowerCase() === 'processing'

  return (
    <div className="bg-white border border-zinc-200 rounded p-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-zinc-100 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-zinc-700" />
            <h3 className="text-sm font-semibold text-zinc-900">{file.filename}</h3>
          </div>
          <div className="text-xs font-mono text-zinc-500 mt-0.5">ID: {file.id}</div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-2.5 py-0.5 rounded font-medium border ${
              isCompleted
                ? 'bg-zinc-100 text-zinc-800 border-zinc-300'
                : isProcessing
                ? 'bg-amber-50 text-amber-800 border-amber-200 animate-pulse'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            {file.status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-3 text-xs">
        <div>
          <div className="text-zinc-500">File Size</div>
          <div className="font-medium text-zinc-800 mt-0.5">{formatBytes(file.file_size)}</div>
        </div>
        <div>
          <div className="text-zinc-500">Source CRS</div>
          <div className="font-medium text-zinc-800 mt-0.5 font-mono">
            {file.source_crs || 'Detecting...'}
          </div>
        </div>
        <div>
          <div className="text-zinc-500">Features Extracted</div>
          <div className="font-medium text-zinc-800 mt-0.5">{file.feature_count}</div>
        </div>
        <div>
          <div className="text-zinc-500">Created At</div>
          <div className="font-medium text-zinc-800 mt-0.5">
            {new Date(file.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      {file.error_message && (
        <div className="mt-3 p-2 text-xs bg-red-50 border border-red-200 text-red-700 rounded">
          <strong>Error:</strong> {file.error_message}
        </div>
      )}
    </div>
  )
}
