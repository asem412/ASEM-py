# 自動化スコアラー (Automation Scorer PWA)

タスクの自動化しやすさを即座に判定するPWAアプリケーション

## 概要

このアプリは、製造・物流・オフィス業務など、様々な業界のタスクについて、自動化の実現性・効果・リスクをルールベースで評価し、スコアと推奨アプローチを提示します。

### 主な機能

- **簡単モード/詳細モード**: 30秒で入力できる簡単モードと、より詳細な分析が可能な詳細モード
- **3軸スコアリング**: Feasibility(実現性)、Impact(効果)、Risk(リスク)の3軸で評価
- **推奨アプローチTop3**: 入力内容に基づいて最適な自動化手段を提案
- **履歴管理**: 過去の判定結果を保存・検索・編集
- **PWA対応**: スマートフォンのホーム画面に追加して、アプリのように使用可能
- **オフライン対応**: ネットワークがなくても基本機能が動作

## 技術スタック

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **PWA**: next-pwa
- **Storage**: LocalStorage (抽象化レイヤーで将来的にSupabase等に差し替え可能)
- **Testing**: Jest + React Testing Library

## プロジェクト構成

```
.
├── app/                    # Next.js App Router
│   ├── layout.tsx         # グローバルレイアウト
│   ├── page.tsx           # 入力フォーム画面
│   ├── result/
│   │   └── page.tsx       # 結果表示画面
│   ├── history/
│   │   └── page.tsx       # 履歴一覧画面
│   └── case/
│       └── [id]/
│           └── page.tsx   # 詳細画面
├── components/            # 共通UIコンポーネント
│   ├── Navigation.tsx
│   └── ScoreBadge.tsx
├── lib/                   # コアロジック
│   ├── types.ts          # TypeScript型定義
│   ├── scorer.ts         # スコア計算ロジック (Pure Function)
│   └── storage.ts        # データ保存レイヤー (抽象化)
├── rules/
│   └── default.json      # スコアリングルール (外出し可能)
├── __tests__/
│   └── scorer.test.ts    # ユニットテスト
└── public/
    ├── manifest.json     # PWAマニフェスト
    └── icons/            # アプリアイコン
```

## セットアップ

### 必要環境

- Node.js 18.x 以上
- npm または yarn

### インストール

```bash
# 依存パッケージのインストール
npm install
```

### 開発サーバーの起動

```bash
npm run dev
```

ブラウザで `http://localhost:3000` を開いてください。

### ビルド

```bash
npm run build
```

### 本番環境での起動

```bash
npm run build
npm start
```

### テストの実行

```bash
# 全テストを実行
npm test

# ウォッチモードでテスト
npm run test:watch
```

## 使い方

### 1. タスクの入力

- **簡単モード**: 9つの基本項目を選択（約30秒）
- **詳細モード**: さらに6つの詳細項目を追加入力

### 2. 判定結果の確認

- 総合スコア (0-100)
- 3軸スコア (Feasibility/Impact/Risk)
- スコアに影響した要因の可視化
- 推奨アプローチTop3
- 追加で確認すべき事項

### 3. 履歴の管理

- 過去の判定結果を一覧表示
- スコアでフィルタリング
- タイトル・メモの編集

## ルールのカスタマイズ

`rules/default.json` を編集することで、スコアリングルールをカスタマイズできます。

### ルールの構成

- **feasibilityRules**: 実現性スコアの計算ルール
- **impactRules**: 効果スコアの計算ルール
- **riskRules**: リスクスコアの計算ルール
- **approachTriggers**: 推奨アプローチの選定条件
- **additionalQuestionTemplates**: 追加質問のテンプレート
- **conclusions**: スコア帯ごとの結論メッセージ

### 例: ルールの追加

```json
{
  "field": "variability",
  "valueScores": {
    "Low": 30,
    "Medium": 15,
    "High": -10
  },
  "reason": "作業のばらつきが低いほど自動化しやすい"
}
```

## ストレージの差し替え

現在はlocalStorageを使用していますが、`lib/storage.ts` の `IStorage` インターフェースを実装することで、簡単に別のストレージに差し替えられます。

### Supabaseへの差し替え例

```typescript
import { createClient } from '@supabase/supabase-js'
import { IStorage, AssessmentCase } from './types'

export class SupabaseStorage implements IStorage {
  private supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

  async saveCase(assessmentCase: AssessmentCase): Promise<void> {
    await this.supabase
      .from('assessment_cases')
      .upsert(assessmentCase)
  }

  // ... 他のメソッドを実装
}

// lib/storage.tsで差し替え
export function getStorage(): IStorage {
  return new SupabaseStorage()
}
```

## PWAとしてインストール

### iOS (Safari)

1. Safariでアプリを開く
2. 共有ボタンをタップ
3. 「ホーム画面に追加」を選択

### Android (Chrome)

1. Chromeでアプリを開く
2. メニュー (⋮) をタップ
3. 「ホーム画面に追加」を選択

## スコアリングロジック

### 総合スコアの計算式

```
TotalScore = (Feasibility × 0.5 + Impact × 0.4 - Risk × 0.3)
```

- 0-100にクリップ
- Feasibility: 実現のしやすさ（高いほど良い）
- Impact: 自動化の効果（高いほど良い）
- Risk: 導入リスク（高いほど悪い）

### スコア帯と判定

- **80-100**: 自動化に非常に適している
- **60-79**: 自動化効果が見込める
- **40-59**: 半自動化から検討
- **20-39**: 現時点では難しい
- **0-19**: 自動化は困難

## ライセンス

MIT

## 今後の拡張案

- [ ] 画像アップロード機能（作業現場の写真）
- [ ] タグ機能の強化
- [ ] 詳細レポートのPDF出力
- [ ] 複数ルールセットの切り替え（業界別）
- [ ] チーム共有機能（Supabase等を使用）
- [ ] 多言語対応

## 開発者向けメモ

### テストのカバレッジ目標

- スコア計算ロジック: 100%
- UIコンポーネント: 基本的な動作確認のみ（時間があれば拡充）

### パフォーマンス最適化

- 画像の遅延読み込み（将来的に画像対応時）
- Service Workerによるキャッシュ戦略
- コード分割（ルート単位）

## お問い合わせ

バグ報告や機能要望は、GitHubのIssueでお願いします。