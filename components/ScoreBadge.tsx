interface ScoreBadgeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export default function ScoreBadge({
  score,
  size = 'md',
  showLabel = false,
}: ScoreBadgeProps) {
  const getColorClass = () => {
    if (score >= 60) return 'score-high'
    if (score >= 40) return 'score-medium'
    return 'score-low'
  }

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'w-12 h-12 text-lg'
      case 'lg':
        return 'w-20 h-20 text-3xl'
      default:
        return 'w-16 h-16 text-2xl'
    }
  }

  return (
    <div className="flex flex-col items-center">
      <div className={`score-badge ${getColorClass()} ${getSizeClass()}`}>
        {score}
      </div>
      {showLabel && (
        <span className="text-xs text-gray-600 mt-1">総合スコア</span>
      )}
    </div>
  )
}
