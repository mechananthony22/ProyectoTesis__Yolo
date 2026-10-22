import {test, expect} from '@playwright/test'

test('login, dataset import, annotation and responsive navigation', async ({page}, testInfo)=>{
 const collectionName=`Smoke test ${testInfo.retry}-${Date.now()} · imágenes sintéticas`
 const pageErrors:string[]=[]
 page.on('pageerror',error=>pageErrors.push(error.message))
 await page.goto('/')
 await page.getByLabel('Usuario',{exact:true}).fill('smoke')
 await page.getByLabel('Contraseña',{exact:true}).fill('Smoke-only-password-29')
 await page.getByRole('button',{name:'Entrar al laboratorio'}).click()
 await expect(page.getByRole('heading',{name:/Hola, smoke/})).toBeVisible()
 await page.getByRole('link',{name:'Mis datasets',exact:true}).click()
 await page.getByRole('button',{name:'Registrar colección'}).click()
 await page.getByPlaceholder('Paltas Hass · Dataset de tesis').fill(collectionName)
 await page.getByRole('button',{name:'Guardar colección'}).click()
 await page.getByRole('link').filter({hasText:collectionName}).click()
 await page.locator('input[type=file]').setInputFiles({name:'fixture.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAHgAAABQCAIAAABd+SbeAAAAzElEQVR4nO3QQRHAIADAMEDXlCAH5VOx8liioNe5zzP43rod8BdGR4yOGB0xOmJ0xOiI0RGjI0ZHjI4YHTE6YnTE6IjREaMjRkeMjhgdMTpidMToiNERoyNGR4yOGB0xOmJ0xOiI0RGjI0ZHjI4YHTE6YnTE6IjREaMjRkeMjhgdMTpidMToiNERoyNGR4yOGB0xOmJ0xOiI0RGjI0ZHjI4YHTE6YnTE6IjREaMjRkeMjhgdMTpidMToiNERoyNGR4yOGB0xOmJ0xOjICxyPAbjJbgMjAAAAAElFTkSuQmCC','base64')})
 await page.getByRole('button',{name:/Importar 1 archivo/}).click()
 await expect(page.getByText('Importadas: 1.',{exact:false})).toBeVisible()
 await page.getByRole('link').filter({hasText:'fixture.png'}).click()
 await expect(page.getByRole('heading',{name:'Revisar y anotar'})).toBeVisible()
 await page.getByPlaceholder('Ejemplo: L01-F023').fill('F001')
 await page.locator('select').first().selectOption('healthy')
 await page.getByRole('button',{name:'Guardar revisión'}).click()
 await expect(page.getByText('Revisión guardada.',{exact:false})).toBeVisible()
 for(const name of ['Preprocesamiento','Entrenamientos','Modelos','Nueva inspección','Historial','Evaluación','Reportes','Trabajos','Configuración']){
  await page.getByRole('link',{name,exact:true}).click()
  await expect(page.locator('main h1')).toBeVisible()
 }
 await page.setViewportSize({width:390,height:844})
 await page.getByRole('button',{name:'Abrir menú'}).click()
 await page.getByRole('link',{name:'Vista general',exact:true}).click()
 await expect(page.getByRole('heading',{name:/Hola, smoke/})).toBeVisible()
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true)
 await testInfo.attach('mobile-dashboard',{body:await page.screenshot({fullPage:true}),contentType:'image/png'})
 expect(pageErrors).toEqual([])
})
