'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { AssessmentCase } from '@/lib/types'
import { getStorage } from '@/lib/storage'
import ScoreBadge from '@/components/ScoreBadge'
import Link from 'next/link'

export default function ResultPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const id = searchParams?.get('id')

  const [assessmentCase, setAssessmentCase] = useState<AssessmentCase | null>(
    null
  )

  useEffect(() => {
    if (id) {
      getStorage()
        .getCase(id)
        .then((data) => setAssessmentCase(data))
    }
  }, [id])

  if (!assessmentCase) {
    return (
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="text-center">読み込み中...</div>
      </div>
    )
  }

  const { result } = assessmentCase

  return (
    <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">判定結果</h1>
        <Link href={`/case/${id}`} className="text-primary-600 text-sm">
          詳細を見る
        </Link>
      </div>

      {/* Total score */}
      <div className="card text-center">
        <ScoreBadge score={result.totalScore} size="lg" showLabel />
        <p className="mt-4 text-lg text-gray-800 font-medium">
          {result.conclusion}
        </p>
      </div>

      {/* 3-axis scores */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          詳細スコア
        </h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                実現性 (Feasibility)
              </span>
              <span className="text-lg font-bold text-primary-600">
                {Math.round(result.feasibility.score)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full"
                style={{ width: `${result.feasibility.score}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                効果 (Impact)
              </span>
              <span className="text-lg font-bold text-green-600">
                {Math.round(result.impact.score)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${result.impact.score}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                リスク (Risk)
              </span>
              <span className="text-lg font-bold text-red-600">
                {Math.round(result.risk.score)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-600 h-2 rounded-full"
                style={{ width: `${result.risk.score}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Top factors */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          スコアに影響した主な要因
        </h2>
        <div className="space-y-3">
          {[...result.feasibility.factors, ...result.impact.factors]
            .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
            .slice(0, 5)
            .map((factor, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-2 bg-gray-50 rounded"
              >
                <span
                  className={`text-lg font-bold ${
                    factor.impact > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {factor.impact > 0 ? '+' : ''}
                  {factor.impact}
                </span>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">
                    {factor.field}: {factor.value}
                  </div>
                  <div className="text-xs text-gray-600">{factor.reason}</div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Recommended approaches */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          推奨アプローチ Top3
        </h2>
        <div className="space-y-3">
          {result.topApproaches.map((approach, index) => (
            <div
              key={index}
              className="p-3 border-l-4 border-primary-500 bg-primary-50 rounded"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-flex items-center justify-center w-6 h-6 bg-primary-600 text-white text-xs font-bold rounded-full">
                  {index + 1}
                </span>
                <span className="font-semibold text-gray-900">
                  {approach.description}
                </span>
              </div>
              <p className="text-sm text-gray-700 ml-8">
                {approach.rationale}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Additional questions */}
      {result.additionalQuestions.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            追加で確認すべき事項
          </h2>
          <ul className="space-y-2">
            {result.additionalQuestions.map((question, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-primary-600 mt-0.5">•</span>
                <span>{question}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => router.push('/')}
          className="btn-secondary flex-1"
        >
          新規判定
        </button>
        <Link href="/history" className="btn-primary flex-1 text-center">
          履歴を見る
        </Link>
      </div>
    </div>
  )
}
