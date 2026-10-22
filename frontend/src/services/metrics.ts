export function formatMetric(value: unknown, digits=4): string {
 if(value===null||value===undefined||value==='')return 'No medida'
 const number=Number(value)
 return Number.isFinite(number)?number.toFixed(digits):'No medida'
}
