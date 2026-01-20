import {
  TaskInput,
  ScoringResult,
  ScoringRules,
  AxisScore,
  ScoreFactor,
  ApproachRecommendation,
} from './types'

/**
 * Calculate automation score based on task input and rules
 * Pure function for easy testing
 */
export function calculateScore(
  input: TaskInput,
  rules: ScoringRules
): ScoringResult {
  // Calculate 3-axis scores
  const feasibility = calculateAxisScore(
    input,
    rules.feasibilityRules,
    'Feasibility'
  )
  const impact = calculateAxisScore(input, rules.impactRules, 'Impact')
  const risk = calculateAxisScore(input, rules.riskRules, 'Risk')

  // Calculate total score: (Feasibility*0.5 + Impact*0.4 - Risk*0.3)
  // Normalize to 0-100
  const rawTotal =
    feasibility.score * 0.5 + impact.score * 0.4 - risk.score * 0.3
  const totalScore = Math.max(0, Math.min(100, rawTotal))

  // Get conclusion
  const conclusion = getConclusion(totalScore, rules.conclusions)

  // Get top 3 approaches
  const topApproaches = getTopApproaches(input, rules.approachTriggers)

  // Get additional questions
  const additionalQuestions = getAdditionalQuestions(
    input,
    rules.additionalQuestionTemplates
  )

  return {
    totalScore: Math.round(totalScore),
    feasibility,
    impact,
    risk,
    conclusion,
    topApproaches,
    additionalQuestions,
  }
}

/**
 * Calculate score for one axis
 */
function calculateAxisScore(
  input: TaskInput,
  axisRules: any[],
  axisName: string
): AxisScore {
  const factors: ScoreFactor[] = []
  let totalScore = 0

  // Combine simple and advanced inputs
  const allInputs: Record<string, any> = {
    ...input.simple,
    ...(input.advanced || {}),
  }

  for (const rule of axisRules) {
    const value = allInputs[rule.field]
    if (value !== undefined && value !== null) {
      const score = rule.valueScores[value]
      if (score !== undefined) {
        totalScore += score
        factors.push({
          field: rule.field,
          value: String(value),
          impact: score,
          reason: rule.reason,
        })
      }
    }
  }

  // Normalize to 0-100 (assuming max possible is around 200, min is around -100)
  const normalizedScore = ((totalScore + 100) / 300) * 100
  const clampedScore = Math.max(0, Math.min(100, normalizedScore))

  // Sort factors by absolute impact
  factors.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))

  return {
    score: clampedScore,
    factors,
  }
}

/**
 * Get conclusion text based on total score
 */
function getConclusion(
  totalScore: number,
  conclusions: any[]
): string {
  for (const conclusion of conclusions) {
    const [min, max] = conclusion.scoreRange
    if (totalScore >= min && totalScore <= max) {
      return conclusion.text
    }
  }
  return '判定結果を確認してください。'
}

/**
 * Get top 3 recommended approaches
 */
function getTopApproaches(
  input: TaskInput,
  triggers: any[]
): ApproachRecommendation[] {
  const allInputs: Record<string, any> = {
    ...input.simple,
    ...(input.advanced || {}),
  }

  const scoredApproaches = triggers.map((trigger) => {
    let matchScore = 0

    for (const condition of trigger.conditions) {
      const value = allInputs[condition.field]
      if (value && condition.values.includes(value)) {
        matchScore += condition.weight || 1
      }
    }

    return {
      category: trigger.category,
      priority: matchScore,
      description: trigger.description,
      rationale: trigger.rationale,
    }
  })

  // Sort by priority and take top 3
  scoredApproaches.sort((a, b) => b.priority - a.priority)
  return scoredApproaches.slice(0, 3)
}

/**
 * Get additional questions based on input
 */
function getAdditionalQuestions(
  input: TaskInput,
  templates: any[]
): string[] {
  const allInputs: Record<string, any> = {
    ...input.simple,
    ...(input.advanced || {}),
  }

  const questions: string[] = []

  for (const template of templates) {
    const value = allInputs[template.condition.field]
    if (value && template.condition.values.includes(value)) {
      questions.push(template.question)
    }
  }

  return questions
}
