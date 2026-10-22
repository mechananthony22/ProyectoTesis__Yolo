import {describe,it,expect} from 'vitest'
import {usePage} from './usePage'
describe('page action notifications',()=>{
 it('preserves a success message produced by the operation',async()=>{
  const page=usePage()
  await page.act(async()=>{page.success.value='Importadas: 1.'})
  expect(page.success.value).toBe('Importadas: 1.')
  expect(page.busy.value).toBe(false)
 })
 it('uses an explicit completion message and clears a previous error',async()=>{
  const page=usePage();page.error.value='previous error'
  await page.act(async()=>{},'Revisión guardada.')
  expect(page.success.value).toBe('Revisión guardada.')
  expect(page.error.value).toBe('')
 })
 it('shows failures and resets the loading state',async()=>{
  const page=usePage();page.success.value='old success'
  await page.act(async()=>{throw new Error('La imagen cambió.')})
  expect(page.error.value).toBe('La imagen cambió.')
  expect(page.success.value).toBe('')
  expect(page.busy.value).toBe(false)
 })
})
