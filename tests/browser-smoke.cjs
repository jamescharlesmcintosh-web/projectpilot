// Optional: start app with an empty test data directory on port 8000; run from the project root with Playwright installed.
const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await b.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000/projects');await page.getByTestId('new-project-btn').click();await page.getByTestId('form-name').fill('Browser verification');await page.getByTestId('form-brief').fill('Build a small interactive counter.');await page.getByTestId('submit-project-btn').click();await page.waitForURL('**/overview');
 await page.getByTestId('nav-master-plan').click();await page.getByTestId('generate-master-btn').click();await page.getByRole('button',{name:'Adopt this version'}).click();await page.getByText('Adopted',{exact:true}).waitFor();
 await page.getByTestId('nav-delegation-plan').click();await page.getByTestId('generate-delegation-btn').click();await page.getByTestId('materialize-btn').click();
 await page.getByTestId('nav-task-queue').click();await page.getByRole('link',{name:'Establish the project foundation'}).click();await page.getByTestId('import-json').fill(fs.readFileSync('examples/first-task-result.json','utf8'));await page.getByTestId('import-btn').click();await page.getByRole('button',{name:'Preview candidate'}).click();await page.waitForURL('**/preview');
 const frame=page.frameLocator('iframe');await frame.getByRole('button',{name:'Take one step'}).click();await frame.getByText('1 step',{exact:true}).waitFor();
 await page.getByTestId('nav-task-queue').click();await page.getByRole('link',{name:'Establish the project foundation'}).click();await page.getByRole('checkbox').check();await page.getByTestId('approve-btn').click();await page.getByText(/^Commit [a-f0-9]{40}$/).waitFor();
 const routes=['/','/projects','/overview','/master-plan','/delegation','/tasks','/preview','/verification','/git','/usage','/activity','/settings'];
 for(const route of routes){await page.goto('http://127.0.0.1:8000'+route);await page.locator('main h1').waitFor();}
 await page.screenshot({path:'preview-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:8000/tasks');await page.locator('main h1').waitFor();await page.getByTestId('sidebar-mobile-toggle').click();await page.getByTestId('nav-usage-cost').click();await page.locator('main h1').waitFor();
 const report={workflow:'create → scaffold → adopt → delegate → import real files → interactive preview → human approval → local commit',routes:routes.length,mobile_navigation:true,browser_errors:errors};fs.writeFileSync('browser-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));await b.close();if(errors.length)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
