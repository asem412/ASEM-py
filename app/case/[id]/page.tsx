'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AssessmentCase } from '@/lib/types'
import { getStorage } from '@/lib/storage'
import ScoreBadge from '@/components/ScoreBadge'
import Link from 'next/link'

export default function CaseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const [assessmentCase, setAssessmentCase] = useState<AssessmentCase | null>(
    null
  )
  const [isEditingMemo, setIsEditingMemo] = useState(false)
  const [memo, setMemo] = useState('')
  const [title, setTitle] = useState('')
  const [isEditingTitle, setIsEditingTitle] = useState(false)

  useEffect(() => {
    if (id) {
      loadCase()
    }
  }, [id])

  const loadCase = async () => {
    const data = await getStorage().getCase(id)
    if (data) {
      setAssessmentCase(data)
      setMemo(data.memo || '')
      setTitle(data.title || '')
    }
  }

  const handleSaveMemo = async () => {
    if (assessmentCase) {
      await getStorage().updateCase(id, { memo })
      setIsEditingMemo(false)
      await loadCase()
    }
  }

  const handleSaveTitle = async () => {
    if (assessmentCase) {
      await getStorage().updateCase(id, { title })
      setIsEditingTitle(false)
      await loadCase()
    }
  }

  const handleDelete = async () => {
    if (confirm('この判定結果を削除しますか？')) {
      await getStorage().deleteCase(id)
      router.push('/history')
    }
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

  const getFieldLabel = (field: string): string => {
    const labels: Record<string, string> = {
      taskType: '作業種類',
      variability: 'ばらつき',
      environment: '作業環境',
      precisionRequired: '精度要求',
      safetyRisk: '安全リスク',
      volumePerMonth: '月間処理量',
      cycleTime: '1サイクルの時間',
      integrationNeed: 'システム連携',
      budgetRange: '予算目安',
      inputStandardization: '入力標準化',
      qualityCriticality: '品質クリティカル度',
      setupChangeFrequency: '段取り替え頻度',
      requiredFlexibility: '柔軟性要求',
      dataAvailability: 'データ蓄積',
      humanSkillDependence: '属人性',
    }
    return labels[field] || field
  }

  if (!assessmentCase) {
    return (
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="text-center">読み込み中...</div>
      </div>
    )
  }

  const { input, result } = assessmentCase

  return (
    <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link
          href="/history"
          className="text-primary-600 flex items-center gap-1"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span>戻る</span>
        </Link>
        <button
          onClick={handleDelete}
          className="text-red-600 text-sm hover:text-red-700"
        >
          削除
        </button>
      </div>

      {/* Title */}
      <div className="card">
        {isEditingTitle ? (
          <div className="space-y-2">
            <input
              type="text"
              className="input-field"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="タイトルを入力..."
            />
            <div className="flex gap-2">
              <button onClick={handleSaveTitle} className="btn-primary text-sm">
                保存
              </button>
              <button
                onClick={() => {
                  setIsEditingTitle(false)
                  setTitle(assessmentCase.title || '')
                }}
                className="btn-secondary text-sm"
              >
                キャンセル
              </button>
            </div>
          </div>
        ) : (
          <div
            className="cursor-pointer"
            onClick={() => setIsEditingTitle(true)}
          >
            <h1 className="text-xl font-bold text-gray-900">
              {assessmentCase.title || result.conclusion}
            </h1>
            <p className="text-xs text-gray-500 mt-1">
              {formatDate(assessmentCase.createdAt)}
            </p>
          </div>
        )}
      </div>

      {/* Score summary */}
      <div className="card text-center">
        <ScoreBadge score={result.totalScore} size="lg" showLabel />
        <p className="mt-4 text-lg text-gray-800 font-medium">
          {result.conclusion}
        </p>
      </div>

      {/* Input details */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">入力内容</h2>
        <div className="space-y-2 text-sm">
          {Object.entries(input.simple).map(([key, value]) => (
            <div key={key} className="flex justify-between py-1 border-b">
              <span className="text-gray-600">{getFieldLabel(key)}</span>
              <span className="font-medium text-gray-900">{String(value)}</span>
            </div>
          ))}
          {input.advanced &&
            Object.entries(input.advanced).map(([key, value]) => {
              if (key === 'constraintsFreeText' && !value) return null
              return (
                <div key={key} className="flex justify-between py-1 border-b">
                  <span className="text-gray-600">{getFieldLabel(key)}</span>
                  <span className="font-medium text-gray-900">
                    {String(value)}
                  </span>
                </div>
              )
            })}
        </div>
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

      {/* Recommended approaches */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          推奨アプローチ
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

      {/* Memo */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">メモ</h2>
        {isEditingMemo ? (
          <div className="space-y-2">
            <textarea
              className="input-field"
              rows={4}
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
              placeholder="メモを入力..."
            />
            <div className="flex gap-2">
              <button onClick={handleSaveMemo} className="btn-primary text-sm">
                保存
              </button>
              <button
                onClick={() => {
                  setIsEditingMemo(false)
                  setMemo(assessmentCase.memo || '')
                }}
                className="btn-secondary text-sm"
              >
                キャンセル
              </button>
            </div>
          </div>
        ) : (
          <div
            className="cursor-pointer min-h-[60px] p-2 rounded hover:bg-gray-50"
            onClick={() => setIsEditingMemo(true)}
          >
            {assessmentCase.memo ? (
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {assessmentCase.memo}
              </p>
            ) : (
              <p className="text-sm text-gray-400">
                クリックしてメモを追加...
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
