import {describe,it,expect} from 'vitest'
import {formatMetric} from './metrics'
describe('research metric formatting',()=>{
 it('keeps undefined metrics distinct from zero',()=>{
  expect(formatMetric(null)).toBe('No medida')
  expect(formatMetric(undefined)).toBe('No medida')
  expect(formatMetric(0)).toBe('0.0000')
 })
 it('never renders NaN or infinity as a measurement',()=>{
  expect(formatMetric(NaN)).toBe('No medida')
  expect(formatMetric(Infinity)).toBe('No medida')
 })
 it('formats actual numeric measurements',()=>expect(formatMetric(.812345)).toBe('0.8123'))
})
