import React, { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import type { FileResponse, PaginatedMeasurementsResponse } from './types'
import { Header } from './components/Header'
import { FileUploadCard } from './components/FileUploadCard'
import { FileLookupCard } from './components/FileLookupCard'
import { FileMetadataCard } from './components/FileMetadataCard'
import { MeasurementsTable } from './components/MeasurementsTable'

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState<boolean>(false)
  const [fileIdInput, setFileIdInput] = useState<string>('')
  const [activeFile, setActiveFile] = useState<FileResponse | null>(null)
  const [measurements, setMeasurements] = useState<PaginatedMeasurementsResponse | null>(null)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(10)
  const [loadingMeasurements, setLoadingMeasurements] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [polling, setPolling] = useState<boolean>(false)

  // Polling for processing completion
  useEffect(() => {
    let intervalId: any
    if (activeFile && (activeFile.status.toLowerCase() === 'processing' || polling)) {
      intervalId = setInterval(() => {
        refreshMetadata(activeFile.id, false)
      }, 2000)
    }
    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [activeFile?.id, activeFile?.status, polling])

  // Fetch measurements when file reaches COMPLETED
  useEffect(() => {
    if (activeFile && activeFile.status.toLowerCase() === 'completed') {
      fetchMeasurements(activeFile.id, page)
    } else {
      setMeasurements(null)
    }
  }, [activeFile?.id, activeFile?.status, page])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) {
      setError('Please select a .kml or .zip Shapefile first.')
      return
    }

    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const res = await fetch('/api/files/', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(errData?.detail || `Upload failed with status ${res.status}`)
      }

      const data: FileResponse = await res.json()
      setActiveFile(data)
      setFileIdInput(data.id)
      setPage(1)
      setSelectedFile(null)
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.')
    } finally {
      setUploading(false)
    }
  }

  const refreshMetadata = async (id: string, showLoading = true) => {
    if (!id.trim()) return
    if (showLoading) setError(null)

    try {
      const res = await fetch(`/api/files/${id.trim()}`)
      if (!res.ok) {
        if (res.status === 404) throw new Error(`File ID "${id}" not found.`)
        throw new Error(`Failed to retrieve file metadata (${res.status}).`)
      }
      const data: FileResponse = await res.json()
      setActiveFile(data)
      if (data.status.toLowerCase() !== 'processing') {
        setPolling(false)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch file metadata.')
    }
  }

  const fetchMeasurements = async (id: string, targetPage: number) => {
    setLoadingMeasurements(true)
    setError(null)
    try {
      const res = await fetch(
        `/api/files/${id}/measurements?page=${targetPage}&page_size=${pageSize}`
      )
      if (!res.ok) {
        throw new Error(`Failed to load measurements (${res.status}).`)
      }
      const data: PaginatedMeasurementsResponse = await res.json()
      setMeasurements(data)
    } catch (err: any) {
      setError(err.message || 'Error fetching measurements.')
    } finally {
      setLoadingMeasurements(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {error && (
          <div className="p-3 text-sm bg-red-50 border border-red-200 text-red-700 rounded flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-xs text-red-600 hover:underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Ingestion & Lookup */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FileUploadCard
            selectedFile={selectedFile}
            uploading={uploading}
            onFileSelect={setSelectedFile}
            onUpload={handleUpload}
          />

          <FileLookupCard
            fileIdInput={fileIdInput}
            activeFile={activeFile}
            polling={polling}
            onFileIdChange={setFileIdInput}
            onLookup={refreshMetadata}
          />
        </div>

        {/* Active File Details */}
        {activeFile && <FileMetadataCard file={activeFile} />}

        {/* Feature Measurements Table */}
        {activeFile && activeFile.status.toLowerCase() === 'completed' && (
          <MeasurementsTable
            measurements={measurements}
            loading={loadingMeasurements}
            currentPage={page}
            onPageChange={setPage}
          />
        )}
      </main>
    </div>
  )
}
