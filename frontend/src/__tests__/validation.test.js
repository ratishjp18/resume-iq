import { validateFile, validateJob } from '../utils/validation'

const file = (name, size) => ({ name, size })

describe('validateFile', () => {
  it('accepts PDF and DOCX', () => {
    expect(validateFile(file('cv.pdf', 1000))).toBeNull()
    expect(validateFile(file('CV.DOCX', 1000))).toBeNull()
  })
  it('rejects unsupported types', () => {
    expect(validateFile(file('cv.txt', 10))).toMatch(/Unsupported/)
  })
  it('rejects empty and oversized files', () => {
    expect(validateFile(file('cv.pdf', 0))).toMatch(/empty/)
    expect(validateFile(file('cv.pdf', 5 * 1024 * 1024 + 1))).toMatch(/too large/)
  })
})

describe('validateJob', () => {
  it('requires title and a substantial description', () => {
    const e = validateJob({ title: ' ', description: 'short' })
    expect(e.title).toBeTruthy()
    expect(e.description).toBeTruthy()
  })
  it('passes valid input', () => {
    expect(validateJob({ title: 'Dev', description: 'x'.repeat(40) })).toEqual({})
  })
})
