// Task characteristics - Simple Mode
export type TaskType =
  | 'PhysicalHandling'
  | 'Assembly'
  | 'Processing'
  | 'Inspection'
  | 'Packaging'
  | 'Admin'
  | 'DataEntry'
  | 'Communication'

export type Variability = 'Low' | 'Medium' | 'High'
export type Environment = 'Clean' | 'Normal' | 'Harsh'
export type PrecisionRequired = 'Loose' | 'Medium' | 'Tight'
export type SafetyRisk = 'None' | 'Low' | 'Medium' | 'High'
export type VolumePerMonth = '<100' | '100-1000' | '1000-10000' | '>10000'
export type CycleTime = '<15s' | '15-60s' | '1-5m' | '>5m'
export type IntegrationNeed = 'None' | 'Some' | 'High'
export type BudgetRange = '<0.3M' | '0.3-1M' | '1-5M' | '>5M'

// Task characteristics - Advanced Mode
export type InputStandardization = 'AlreadyStandardized' | 'CanStandardize' | 'HardToStandardize'
export type QualityCriticality = 'Low' | 'Medium' | 'High'
export type SetupChangeFrequency = 'Rare' | 'Weekly' | 'Daily' | 'ManyPerDay'
export type RequiredFlexibility = 'Low' | 'Medium' | 'High'
export type DataAvailability = 'None' | 'Some' | 'Plenty'
export type HumanSkillDependence = 'Low' | 'Medium' | 'High'

// Input form data
export interface SimpleInput {
  taskType: TaskType
  variability: Variability
  environment: Environment
  precisionRequired: PrecisionRequired
  safetyRisk: SafetyRisk
  volumePerMonth: VolumePerMonth
  cycleTime: CycleTime
  integrationNeed: IntegrationNeed
  budgetRange: BudgetRange
}

export interface AdvancedInput {
  inputStandardization: InputStandardization
  qualityCriticality: QualityCriticality
  setupChangeFrequency: SetupChangeFrequency
  requiredFlexibility: RequiredFlexibility
  dataAvailability: DataAvailability
  humanSkillDependence: HumanSkillDependence
  constraintsFreeText?: string
}

export interface TaskInput {
  simple: SimpleInput
  advanced?: AdvancedInput
  mode: 'simple' | 'advanced'
}

// Scoring results
export interface AxisScore {
  score: number // 0-100
  factors: ScoreFactor[]
}

export interface ScoreFactor {
  field: string
  value: string
  impact: number
  reason: string
}

export interface ScoringResult {
  totalScore: number // 0-100
  feasibility: AxisScore
  impact: AxisScore
  risk: AxisScore
  conclusion: string
  topApproaches: ApproachRecommendation[]
  additionalQuestions: string[]
}

export interface ApproachRecommendation {
  category: ApproachCategory
  priority: number
  description: string
  rationale: string
}

export type ApproachCategory =
  | 'Standardize'
  | 'SemiAutomation'
  | 'Robot'
  | 'Software'
  | 'Sensing'

// Assessment case (for history)
export interface AssessmentCase {
  id: string
  createdAt: string
  updatedAt: string
  input: TaskInput
  result: ScoringResult
  tags?: string[]
  memo?: string
  title?: string
}

// Rules schema
export interface ScoringRules {
  feasibilityRules: FieldRule[]
  impactRules: FieldRule[]
  riskRules: FieldRule[]
  approachTriggers: ApproachTrigger[]
  additionalQuestionTemplates: QuestionTemplate[]
  conclusions: ConclusionTemplate[]
}

export interface FieldRule {
  field: string
  valueScores: Record<string, number>
  reason: string
}

export interface ApproachTrigger {
  category: ApproachCategory
  conditions: TriggerCondition[]
  description: string
  rationale: string
}

export interface TriggerCondition {
  field: string
  values: string[]
  weight?: number
}

export interface QuestionTemplate {
  condition: {
    field: string
    values: string[]
  }
  question: string
}

export interface ConclusionTemplate {
  scoreRange: [number, number]
  text: string
}
