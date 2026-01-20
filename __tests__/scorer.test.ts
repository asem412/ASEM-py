import { calculateScore } from '@/lib/scorer'
import { TaskInput, ScoringRules } from '@/lib/types'
import defaultRules from '@/rules/default.json'

describe('Scorer', () => {
  const rules = defaultRules as ScoringRules

  describe('calculateScore', () => {
    it('should give high score for ideal automation task', () => {
      const input: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'Admin',
          variability: 'Low',
          environment: 'Clean',
          precisionRequired: 'Loose',
          safetyRisk: 'None',
          volumePerMonth: '>10000',
          cycleTime: '>5m',
          integrationNeed: 'None',
          budgetRange: '1-5M',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.totalScore).toBeGreaterThan(60)
      expect(result.feasibility.score).toBeGreaterThan(50)
      expect(result.impact.score).toBeGreaterThan(50)
      expect(result.risk.score).toBeLessThan(30)
    })

    it('should give low score for difficult automation task', () => {
      const input: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'Assembly',
          variability: 'High',
          environment: 'Harsh',
          precisionRequired: 'Tight',
          safetyRisk: 'High',
          volumePerMonth: '<100',
          cycleTime: '<15s',
          integrationNeed: 'High',
          budgetRange: '<0.3M',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.totalScore).toBeLessThan(50)
      expect(result.risk.score).toBeGreaterThan(40)
    })

    it('should include feasibility factors in result', () => {
      const input: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'Processing',
          variability: 'Low',
          environment: 'Normal',
          precisionRequired: 'Medium',
          safetyRisk: 'Low',
          volumePerMonth: '1000-10000',
          cycleTime: '1-5m',
          integrationNeed: 'Some',
          budgetRange: '0.3-1M',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.feasibility.factors.length).toBeGreaterThan(0)
      expect(result.feasibility.factors[0]).toHaveProperty('field')
      expect(result.feasibility.factors[0]).toHaveProperty('value')
      expect(result.feasibility.factors[0]).toHaveProperty('impact')
      expect(result.feasibility.factors[0]).toHaveProperty('reason')
    })

    it('should return top 3 approaches', () => {
      const input: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'Admin',
          variability: 'Medium',
          environment: 'Normal',
          precisionRequired: 'Medium',
          safetyRisk: 'None',
          volumePerMonth: '100-1000',
          cycleTime: '15-60s',
          integrationNeed: 'None',
          budgetRange: '<0.3M',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.topApproaches).toHaveLength(3)
      expect(result.topApproaches[0]).toHaveProperty('category')
      expect(result.topApproaches[0]).toHaveProperty('description')
      expect(result.topApproaches[0]).toHaveProperty('rationale')
    })

    it('should include additional questions based on input', () => {
      const input: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'Processing',
          variability: 'High',
          environment: 'Harsh',
          precisionRequired: 'Medium',
          safetyRisk: 'High',
          volumePerMonth: '<100',
          cycleTime: '15-60s',
          integrationNeed: 'High',
          budgetRange: '<0.3M',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.additionalQuestions.length).toBeGreaterThan(0)
      expect(typeof result.additionalQuestions[0]).toBe('string')
    })

    it('should handle advanced mode input', () => {
      const input: TaskInput = {
        mode: 'advanced',
        simple: {
          taskType: 'Inspection',
          variability: 'Medium',
          environment: 'Normal',
          precisionRequired: 'Tight',
          safetyRisk: 'Low',
          volumePerMonth: '1000-10000',
          cycleTime: '15-60s',
          integrationNeed: 'Some',
          budgetRange: '1-5M',
        },
        advanced: {
          inputStandardization: 'AlreadyStandardized',
          qualityCriticality: 'High',
          setupChangeFrequency: 'Rare',
          requiredFlexibility: 'Low',
          dataAvailability: 'Plenty',
          humanSkillDependence: 'High',
          constraintsFreeText: 'Test constraint',
        },
      }

      const result = calculateScore(input, rules)

      expect(result.totalScore).toBeGreaterThan(0)
      expect(result.feasibility.factors.some(f => f.field === 'inputStandardization')).toBe(true)
    })

    it('should return appropriate conclusion', () => {
      const highScoreInput: TaskInput = {
        mode: 'simple',
        simple: {
          taskType: 'DataEntry',
          variability: 'Low',
          environment: 'Clean',
          precisionRequired: 'Loose',
          safetyRisk: 'None',
          volumePerMonth: '>10000',
          cycleTime: '>5m',
          integrationNeed: 'None',
          budgetRange: '1-5M',
        },
      }

      const result = calculateScore(highScoreInput, rules)
      expect(result.conclusion).toBeTruthy()
      expect(typeof result.conclusion).toBe('string')
    })
  })
})
