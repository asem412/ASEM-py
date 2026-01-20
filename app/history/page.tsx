'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { AssessmentCase } from '@/lib/types'
import { getStorage } from '@/lib/storage'
import ScoreBadge from '@/components/ScoreBadge'

export default function HistoryPage() {
  const [cases, setCases] = useState<AssessmentCase[]>([])
  const [filteredCases, setFilteredCases] = useState<AssessmentCase[]>([])
  const [scoreFilter, setScoreFilter] = useState<string>('all')

  useEffect(() => {
    loadCases()
  }, [])

  useEffect(() => {
    applyFilters()
  }, [cases, scoreFilter])

  const loadCases = async () => {
    const data = await getStorage().getCases()
    setCases(data)
  }

  const applyFilters = () => {
    let filtered = [...cases]

    if (scoreFilter === 'high') {
      filtered = filtered.filter((c) => c.result.totalScore >= 60)
    } else if (scoreFilter === 'medium') {
      filtered = filtered.filter(
        (c) => c.result.totalScore >= 40 && c.result.totalScore < 60
      )
    } else if (scoreFilter === 'low') {
      filtered = filtered.filter((c) => c.result.totalScore < 40)
    }

    setFilteredCases(filtered)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTaskTypeLabel = (taskType: string) => {
    const labels: Record<string, string> = {
      PhysicalHandling: '物理的搬送',
      Assembly: '組立',
      Processing: '加工',
      Inspection: '検査',
      Packaging: '梱包',
      Admin: '事務',
      DataEntry: 'データ入力',
      Communication: 'コミュニケーション',
    }
    return labels[taskType] || taskType
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">判定履歴</h1>

      {/* Filters */}
      <div className="card mb-6">
        <label className="label">スコアで絞り込み</label>
        <select
          className="select-field"
          value={scoreFilter}
          onChange={(e) => setScoreFilter(e.target.value)}
        >
          <option value="all">すべて</option>
          <option value="high">高スコア (60以上)</option>
          <option value="medium">中スコア (40-59)</option>
          <option value="low">低スコア (40未満)</option>
        </select>
      </div>

      {/* Cases list */}
      {filteredCases.length === 0 ? (
        <div className="card text-center text-gray-500">
          {cases.length === 0
            ? '履歴がありません。まず判定を実行してみましょう。'
            : '該当する履歴がありません。'}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredCases.map((assessmentCase) => (
            <Link
              key={assessmentCase.id}
              href={`/case/${assessmentCase.id}`}
              className="card block hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start gap-4">
                <ScoreBadge score={assessmentCase.result.totalScore} size="sm" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="inline-block px-2 py-0.5 bg-primary-100 text-primary-800 text-xs font-medium rounded">
                      {getTaskTypeLabel(assessmentCase.input.simple.taskType)}
                    </span>
                    {assessmentCase.input.mode === 'advanced' && (
                      <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-800 text-xs font-medium rounded">
                        詳細
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-800 font-medium line-clamp-2 mb-1">
                    {assessmentCase.title || assessmentCase.result.conclusion}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDate(assessmentCase.createdAt)}
                  </p>
                </div>
                <svg
                  className="w-5 h-5 text-gray-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>

              {assessmentCase.memo && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                  メモ: {assessmentCase.memo}
                </p>
              )}

              {assessmentCase.tags && assessmentCase.tags.length > 0 && (
                <div className="flex gap-2 mt-2 flex-wrap">
                  {assessmentCase.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}

      {/* New assessment button */}
      <Link href="/" className="btn-primary w-full py-3 text-lg mt-6 block text-center">
        新規判定
      </Link>
    </div>
  )
}
