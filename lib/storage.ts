import { AssessmentCase } from './types'

/**
 * Storage interface for abstraction
 * Can be replaced with Supabase, Firebase, etc.
 */
export interface IStorage {
  saveCase(assessmentCase: AssessmentCase): Promise<void>
  getCases(): Promise<AssessmentCase[]>
  getCase(id: string): Promise<AssessmentCase | null>
  updateCase(id: string, updates: Partial<AssessmentCase>): Promise<void>
  deleteCase(id: string): Promise<void>
  searchCases(query: {
    dateFrom?: string
    dateTo?: string
    tags?: string[]
    scoreMin?: number
    scoreMax?: number
  }): Promise<AssessmentCase[]>
}

/**
 * LocalStorage implementation
 */
export class LocalStorageImpl implements IStorage {
  private readonly STORAGE_KEY = 'automation-scorer-cases'

  private getCasesFromStorage(): AssessmentCase[] {
    if (typeof window === 'undefined') return []

    const data = localStorage.getItem(this.STORAGE_KEY)
    if (!data) return []

    try {
      return JSON.parse(data)
    } catch {
      return []
    }
  }

  private saveCasesToStorage(cases: AssessmentCase[]): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cases))
  }

  async saveCase(assessmentCase: AssessmentCase): Promise<void> {
    const cases = this.getCasesFromStorage()
    const existingIndex = cases.findIndex((c) => c.id === assessmentCase.id)

    if (existingIndex >= 0) {
      cases[existingIndex] = assessmentCase
    } else {
      cases.push(assessmentCase)
    }

    this.saveCasesToStorage(cases)
  }

  async getCases(): Promise<AssessmentCase[]> {
    return this.getCasesFromStorage().sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    )
  }

  async getCase(id: string): Promise<AssessmentCase | null> {
    const cases = this.getCasesFromStorage()
    return cases.find((c) => c.id === id) || null
  }

  async updateCase(
    id: string,
    updates: Partial<AssessmentCase>
  ): Promise<void> {
    const cases = this.getCasesFromStorage()
    const index = cases.findIndex((c) => c.id === id)

    if (index >= 0) {
      cases[index] = {
        ...cases[index],
        ...updates,
        updatedAt: new Date().toISOString(),
      }
      this.saveCasesToStorage(cases)
    }
  }

  async deleteCase(id: string): Promise<void> {
    const cases = this.getCasesFromStorage()
    const filtered = cases.filter((c) => c.id !== id)
    this.saveCasesToStorage(filtered)
  }

  async searchCases(query: {
    dateFrom?: string
    dateTo?: string
    tags?: string[]
    scoreMin?: number
    scoreMax?: number
  }): Promise<AssessmentCase[]> {
    let cases = this.getCasesFromStorage()

    if (query.dateFrom) {
      const from = new Date(query.dateFrom).getTime()
      cases = cases.filter((c) => new Date(c.createdAt).getTime() >= from)
    }

    if (query.dateTo) {
      const to = new Date(query.dateTo).getTime()
      cases = cases.filter((c) => new Date(c.createdAt).getTime() <= to)
    }

    if (query.tags && query.tags.length > 0) {
      cases = cases.filter((c) =>
        query.tags!.some((tag) => c.tags?.includes(tag))
      )
    }

    if (query.scoreMin !== undefined) {
      cases = cases.filter((c) => c.result.totalScore >= query.scoreMin!)
    }

    if (query.scoreMax !== undefined) {
      cases = cases.filter((c) => c.result.totalScore <= query.scoreMax!)
    }

    return cases.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    )
  }
}

// Singleton instance
let storageInstance: IStorage | null = null

export function getStorage(): IStorage {
  if (!storageInstance) {
    storageInstance = new LocalStorageImpl()
  }
  return storageInstance
}

// For testing or switching to other storage
export function setStorage(storage: IStorage): void {
  storageInstance = storage
}
