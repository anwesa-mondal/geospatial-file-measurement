import React, { useRef } from 'react'
import { Upload, RefreshCw, FileText } from 'lucide-react'
import { formatBytes } from '../lib/formatters'

interface FileUploadCardProps {
  selectedFile: File | null
  uploading: boolean
  onFileSelect: (file: File | null) => void
  onUpload: (e: React.FormEvent) => void
}

export const FileUploadCard: React.FC<FileUploadCardProps> = ({
  selectedFile,
  uploading,
  onFileSelect,
  onUpload,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    onUpload(e)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="bg-white border border-zinc-200 rounded p-4">
      <div className="flex items-center gap-2 mb-3">
        <Upload className="w-4 h-4 text-zinc-600" />
        <h2 className="text-sm font-semibold text-zinc-800 uppercase tracking-wide">
          Upload Geospatial File
        </h2>
      </div>
      <p className="text-xs text-zinc-500 mb-3">
        Ingest standard <code>.kml</code> or packaged <code>.zip</code> Shapefiles (containing .shp, .shx, .dbf).
      </p>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="border border-dashed border-zinc-300 rounded p-4 text-center bg-zinc-50 hover:bg-zinc-100/50 transition-colors">
          <input
            ref={fileInputRef}
            type="file"
            id="file-input"
            accept=".kml,.zip"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="file-input"
            className="cursor-pointer flex flex-col items-center justify-center text-xs text-zinc-600"
          >
            <FileText className="w-6 h-6 text-zinc-400 mb-1" />
            <span className="font-medium text-zinc-700">
              {selectedFile ? selectedFile.name : 'Click to select .kml or .zip'}
            </span>
            {selectedFile && (
              <span className="text-zinc-400 mt-0.5">({formatBytes(selectedFile.size)})</span>
            )}
          </label>
        </div>

        <button
          type="submit"
          disabled={!selectedFile || uploading}
          className="w-full text-xs font-medium py-2 px-3 bg-zinc-900 text-white rounded hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          {uploading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Uploading & Queueing...
            </>
          ) : (
            <>
              <Upload className="w-3.5 h-3.5" />
              Upload & Process
            </>
          )}
        </button>
      </form>
    </div>
  )
}
