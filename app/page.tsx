'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { TaskInput, SimpleInput, AdvancedInput } from '@/lib/types'
import { calculateScore } from '@/lib/scorer'
import { getStorage } from '@/lib/storage'
import defaultRules from '@/rules/default.json'

export default function Home() {
  const router = useRouter()
  const [mode, setMode] = useState<'simple' | 'advanced'>('simple')

  const [simple, setSimple] = useState<SimpleInput>({
    taskType: 'PhysicalHandling',
    variability: 'Medium',
    environment: 'Normal',
    precisionRequired: 'Medium',
    safetyRisk: 'Low',
    volumePerMonth: '100-1000',
    cycleTime: '15-60s',
    integrationNeed: 'Some',
    budgetRange: '0.3-1M',
  })

  const [advanced, setAdvanced] = useState<AdvancedInput>({
    inputStandardization: 'CanStandardize',
    qualityCriticality: 'Medium',
    setupChangeFrequency: 'Weekly',
    requiredFlexibility: 'Medium',
    dataAvailability: 'Some',
    humanSkillDependence: 'Medium',
    constraintsFreeText: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const input: TaskInput = {
      mode,
      simple,
      ...(mode === 'advanced' ? { advanced } : {}),
    }

    const result = calculateScore(input, defaultRules as any)

    // Save to storage
    const assessmentCase = {
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      input,
      result,
    }

    await getStorage().saveCase(assessmentCase)

    // Navigate to result page with case ID
    router.push(`/result?id=${assessmentCase.id}`)
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        自動化スコアラー
      </h1>

      {/* Mode tabs */}
      <div className="flex gap-2 mb-6">
        <button
          type="button"
          onClick={() => setMode('simple')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
            mode === 'simple'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          簡単モード
        </button>
        <button
          type="button"
          onClick={() => setMode('advanced')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
            mode === 'advanced'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          詳細モード
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Simple mode fields */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">基本情報</h2>

          <div>
            <label className="label">作業種類</label>
            <select
              className="select-field"
              value={simple.taskType}
              onChange={(e) =>
                setSimple({ ...simple, taskType: e.target.value as any })
              }
            >
              <option value="PhysicalHandling">物理的な搬送・ハンドリング</option>
              <option value="Assembly">組立・取付</option>
              <option value="Processing">加工・処理</option>
              <option value="Inspection">検査・確認</option>
              <option value="Packaging">梱包・包装</option>
              <option value="Admin">事務作業</option>
              <option value="DataEntry">データ入力</option>
              <option value="Communication">コミュニケーション</option>
            </select>
          </div>

          <div>
            <label className="label">ばらつき（対象物・入力の一貫性）</label>
            <select
              className="select-field"
              value={simple.variability}
              onChange={(e) =>
                setSimple({ ...simple, variability: e.target.value as any })
              }
            >
              <option value="Low">低（ほぼ同じ）</option>
              <option value="Medium">中（やや違う）</option>
              <option value="High">高（毎回違う）</option>
            </select>
          </div>

          <div>
            <label className="label">作業環境</label>
            <select
              className="select-field"
              value={simple.environment}
              onChange={(e) =>
                setSimple({ ...simple, environment: e.target.value as any })
              }
            >
              <option value="Clean">良好（クリーンルーム等）</option>
              <option value="Normal">普通（屋内・一般環境）</option>
              <option value="Harsh">過酷（粉じん・油・熱・屋外等）</option>
            </select>
          </div>

          <div>
            <label className="label">精度要求</label>
            <select
              className="select-field"
              value={simple.precisionRequired}
              onChange={(e) =>
                setSimple({
                  ...simple,
                  precisionRequired: e.target.value as any,
                })
              }
            >
              <option value="Loose">ゆるい（大まか）</option>
              <option value="Medium">普通（±数mm・普通の判断）</option>
              <option value="Tight">厳しい（±0.1mm以下・微妙な判断）</option>
            </select>
          </div>

          <div>
            <label className="label">安全リスク</label>
            <select
              className="select-field"
              value={simple.safetyRisk}
              onChange={(e) =>
                setSimple({ ...simple, safetyRisk: e.target.value as any })
              }
            >
              <option value="None">なし</option>
              <option value="Low">低</option>
              <option value="Medium">中</option>
              <option value="High">高（重機・危険物等）</option>
            </select>
          </div>

          <div>
            <label className="label">月間処理量</label>
            <select
              className="select-field"
              value={simple.volumePerMonth}
              onChange={(e) =>
                setSimple({ ...simple, volumePerMonth: e.target.value as any })
              }
            >
              <option value="<100">100回未満</option>
              <option value="100-1000">100〜1,000回</option>
              <option value="1000-10000">1,000〜10,000回</option>
              <option value=">10000">10,000回以上</option>
            </select>
          </div>

          <div>
            <label className="label">1サイクルの時間</label>
            <select
              className="select-field"
              value={simple.cycleTime}
              onChange={(e) =>
                setSimple({ ...simple, cycleTime: e.target.value as any })
              }
            >
              <option value="<15s">15秒未満</option>
              <option value="15-60s">15秒〜1分</option>
              <option value="1-5m">1〜5分</option>
              <option value=">5m">5分以上</option>
            </select>
          </div>

          <div>
            <label className="label">既存システム連携の必要性</label>
            <select
              className="select-field"
              value={simple.integrationNeed}
              onChange={(e) =>
                setSimple({ ...simple, integrationNeed: e.target.value as any })
              }
            >
              <option value="None">なし（単独で完結）</option>
              <option value="Some">少しあり</option>
              <option value="High">高度な連携が必要</option>
            </select>
          </div>

          <div>
            <label className="label">予算目安</label>
            <select
              className="select-field"
              value={simple.budgetRange}
              onChange={(e) =>
                setSimple({ ...simple, budgetRange: e.target.value as any })
              }
            >
              <option value="<0.3M">30万円未満</option>
              <option value="0.3-1M">30万〜100万円</option>
              <option value="1-5M">100万〜500万円</option>
              <option value=">5M">500万円以上</option>
            </select>
          </div>
        </div>

        {/* Advanced mode fields */}
        {mode === 'advanced' && (
          <div className="card space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">詳細情報</h2>

            <div>
              <label className="label">入力の標準化状況</label>
              <select
                className="select-field"
                value={advanced.inputStandardization}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    inputStandardization: e.target.value as any,
                  })
                }
              >
                <option value="AlreadyStandardized">既に標準化済み</option>
                <option value="CanStandardize">標準化可能</option>
                <option value="HardToStandardize">標準化困難</option>
              </select>
            </div>

            <div>
              <label className="label">品質クリティカル度</label>
              <select
                className="select-field"
                value={advanced.qualityCriticality}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    qualityCriticality: e.target.value as any,
                  })
                }
              >
                <option value="Low">低</option>
                <option value="Medium">中</option>
                <option value="High">高（不良が致命的）</option>
              </select>
            </div>

            <div>
              <label className="label">段取り替え頻度</label>
              <select
                className="select-field"
                value={advanced.setupChangeFrequency}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    setupChangeFrequency: e.target.value as any,
                  })
                }
              >
                <option value="Rare">稀（月1回以下）</option>
                <option value="Weekly">週1回程度</option>
                <option value="Daily">日1回程度</option>
                <option value="ManyPerDay">日に何度も</option>
              </select>
            </div>

            <div>
              <label className="label">柔軟性要求（品種変更・変動対応）</label>
              <select
                className="select-field"
                value={advanced.requiredFlexibility}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    requiredFlexibility: e.target.value as any,
                  })
                }
              >
                <option value="Low">低（固定的）</option>
                <option value="Medium">中</option>
                <option value="High">高（多品種・変動大）</option>
              </select>
            </div>

            <div>
              <label className="label">データ蓄積状況</label>
              <select
                className="select-field"
                value={advanced.dataAvailability}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    dataAvailability: e.target.value as any,
                  })
                }
              >
                <option value="None">なし</option>
                <option value="Some">少しある</option>
                <option value="Plenty">十分ある（ログ・画像・仕様等）</option>
              </select>
            </div>

            <div>
              <label className="label">属人性（職人技への依存）</label>
              <select
                className="select-field"
                value={advanced.humanSkillDependence}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    humanSkillDependence: e.target.value as any,
                  })
                }
              >
                <option value="Low">低（誰でもできる）</option>
                <option value="Medium">中</option>
                <option value="High">高（熟練者のみ）</option>
              </select>
            </div>

            <div>
              <label className="label">その他制約（任意）</label>
              <textarea
                className="input-field"
                rows={3}
                value={advanced.constraintsFreeText}
                onChange={(e) =>
                  setAdvanced({
                    ...advanced,
                    constraintsFreeText: e.target.value,
                  })
                }
                placeholder="スペース制約、法規制、顧客要求など..."
              />
            </div>
          </div>
        )}

        <button type="submit" className="btn-primary w-full py-3 text-lg">
          判定する
        </button>
      </form>
    </div>
  )
}
