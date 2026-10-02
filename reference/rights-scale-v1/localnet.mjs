// Functional acceptance on an explicitly selected disposable loopback chain only.
// Reuses the legacy client's locked tooling, not its business logic or decoders.
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
const here=dirname(fileURLToPath(import.meta.url));
const require=createRequire(resolve(here,'../v0.3-rc1/client/package.json'));
const {SuiGrpcClient}=await import(pathToFileURL(require.resolve('@mysten/sui/grpc')));
const {Transaction}=await import(pathToFileURL(require.resolve('@mysten/sui/transactions')));
const {Ed25519Keypair}=await import(pathToFileURL(require.resolve('@mysten/sui/keypairs/ed25519')));
const {bcs}=await import(pathToFileURL(require.resolve('@mysten/sui/bcs')));
const endpoint=process.env.KIX_LOCAL_RPC;
assert.equal(endpoint,'http://127.0.0.1:9000','explicit disposable loopback RPC required');
const out=process.env.KIX_SCALE_OUTPUT;assert(out,'output path required');
const client=new SuiGrpcClient({network:'localnet',baseUrl:endpoint});
const key=Ed25519Keypair.generate(),sender=key.toSuiAddress();
const chain=await client.getChainIdentifier();
const evidence={profile:'RS-PUBLIC-1',chain,mode:'LOCALNET_FUNCTIONAL',cases:[],transactions:[],production:false};
async function submit(tx,label,expectedAbort){
 tx.setSender(sender);tx.setGasBudget(1000000000);
 // Resolve kind first to avoid pre-execution simulation masking negative cases.
 const kind=await tx.build({client,onlyTransactionKind:true});const full=Transaction.fromKind(kind);
 full.setSender(sender);full.setGasBudget(1000000000);
 const {referenceGasPrice}=await client.getReferenceGasPrice();full.setGasPrice(referenceGasPrice);
 const {objects}=await client.listCoins({owner:sender});const coin=objects.find(c=>BigInt(c.balance)>=1000000000n);assert(coin);
 full.setGasPayment([{objectId:coin.objectId,version:coin.version,digest:coin.digest}]);
 const bytes=await full.build();const {signature}=await key.signTransaction(bytes);
 // One submission; unknown outcome stops the entire run. Never retry a write.
 const result=await client.executeTransaction({transaction:bytes,signatures:[signature],include:{effects:true,events:true,objectTypes:true}});
 await client.waitForTransaction({result,timeout:20000});
 const r=result.Transaction??result.FailedTransaction;assert(r);
 evidence.transactions.push({label,digest:r.digest,status:r.status});
 if(expectedAbort!==undefined){assert.equal(r.status.success,false);assert.equal(String(r.status.error?.MoveAbort?.abortCode),String(expectedAbort));}
 else assert.equal(r.status.success,true,JSON.stringify(r.status));
 return r;
}
const response=await fetch('http://127.0.0.1:9123/v2/gas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({FixedAmountRequest:{recipient:sender}})});assert(response.ok);
let ready=false;for(let i=0;i<50;i++){const {objects}=await client.listCoins({owner:sender});if(objects.some(c=>BigInt(c.balance)>=1000000000n)){ready=true;break;}await new Promise(r=>setTimeout(r,200));}assert(ready);
const built=spawnSync(process.env.KIX_SUI_BIN??'sui',['move','--client.config',process.env.KIX_SUI_CONFIG,'--build-env','mainnet','build','--path',resolve(here,'sui'),'--dump-bytecode-as-base64'],{encoding:'utf8'});assert.equal(built.status,0,built.stderr);
const compiled=JSON.parse(built.stdout);const pubtx=new Transaction();const upgrade=pubtx.publish({modules:compiled.modules,dependencies:compiled.dependencies});pubtx.moveCall({target:'0x2::package::make_immutable',arguments:[upgrade]});
const pub=await submit(pubtx,'publish');const pkg=(pub.effects?.changedObjects??[]).find(x=>x.outputState?.$kind==='PackageWrite'||x.outputState?.PackageWrite)?.objectId??Object.entries(pub.objectTypes??{}).find(([,v])=>v==='package')?.[0];assert(pkg);evidence.package=pkg;
const target=fn=>`${pkg}::rights::${fn}`;
function call(fn,args){const t=new Transaction();t.moveCall({target:target(fn),arguments:args(t)});return t;}
function one(r,suffix){const ids=Object.entries(r.objectTypes??{}).filter(([,v])=>v.endsWith(suffix)).map(([k])=>k);assert.equal(ids.length,1);return ids[0];}
const Page=bcs.struct('InventoryPage',{id:bcs.Address,show:bcs.Address,index:bcs.u64(),start:bcs.u64(),generations:bcs.vector(bcs.u64()),occupied:bcs.vector(bcs.bool()),issued:bcs.u64()});
async function pageData(id){const {object}=await client.getObject({objectId:id,include:{content:true}});assert.equal(object.type,`${pkg}::rights::InventoryPage`);return Page.parse(object.content);}
for(const capacity of [1024,16384,65536]){
 const r=await submit(call('create_show',t=>[t.pure.u64(capacity),t.pure.vector('address',[sender]),t.pure.vector('address',[sender]),t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300)]),`create-${capacity}`);
 const show=one(r,'::rights::ShowControl'),cap=one(r,'::rights::IssuerCap');let pages=[];
 for(let start=0;start<capacity/256;start+=32){const tx=new Transaction();for(let i=start;i<Math.min(start+32,capacity/256);i++)tx.moveCall({target:target('create_page'),arguments:[tx.object(show),tx.object(cap),tx.pure.u64(i)]});const rr=await submit(tx,`pages-${capacity}-${start}`);pages.push(...Object.entries(rr.objectTypes??{}).filter(([,v])=>v.endsWith('::rights::InventoryPage')).map(([id])=>id));}
 assert.equal(pages.length,capacity/256);
 const shards=new Transaction();for(let i=0;i<16;i++)shards.moveCall({target:target('create_payment_shard'),arguments:[shards.object(show),shards.object(cap),shards.pure.u64(i)]});await submit(shards,`shards-${capacity}`);
 await submit(call('seal',t=>[t.object(show),t.object(cap)]),`seal-${capacity}`);
 const indexed=await Promise.all(pages.map(async id=>({id,data:await pageData(id)})));indexed.sort((a,b)=>Number(a.data.index)-Number(b.data.index));
 assert.equal(indexed.reduce((a,p)=>a+p.data.occupied.length,0),capacity);
 for(let i=0;i<indexed.length;i++){assert.equal(Number(indexed[i].data.start),i*256);assert.equal(indexed[i].data.show,show);}
 const last=indexed.at(-1).id,first=indexed[0].id;
 const ir=await submit(call('issue',t=>[t.object(show),t.object(last),t.pure.u64(capacity-1),t.pure.u64(0),t.pure.address(sender)]),`issue-last-${capacity}`);const ticket=one(ir,'::rights::Ticket');
 assert.equal((await pageData(last)).occupied[255],true);
 // Cross-page PTB rollback: the first write is valid, the second collides.
 const bundle=new Transaction();bundle.moveCall({target:target('issue'),arguments:[bundle.object(show),bundle.object(first),bundle.pure.u64(0),bundle.pure.u64(0),bundle.pure.address(sender)]});bundle.moveCall({target:target('issue'),arguments:[bundle.object(show),bundle.object(last),bundle.pure.u64(capacity-1),bundle.pure.u64(0),bundle.pure.address(sender)]});await submit(bundle,`cross-page-rollback-${capacity}`,9);
 assert.equal((await pageData(first)).occupied[0],false);
 await submit(call('refund',t=>[t.object(show),t.object(last),t.object(ticket),t.pure.u64(1),t.object('0x6')]),`refund-${capacity}`);
 await submit(call('issue',t=>[t.object(show),t.object(last),t.pure.u64(capacity-1),t.pure.u64(0),t.pure.address(sender)]),`stale-after-refund-${capacity}`,3);
 await submit(call('issue',t=>[t.object(show),t.object(last),t.pure.u64(capacity-1),t.pure.u64(1),t.pure.address(sender)]),`new-generation-${capacity}`);
 await submit(call('cancel_show',t=>[t.object(show),t.object(cap)]),`cancel-${capacity}`);
 await submit(call('issue',t=>[t.object(show),t.object(first),t.pure.u64(0),t.pure.u64(0),t.pure.address(sender)]),`cancelled-issue-${capacity}`,9);
 evidence.cases.push({capacity,pages:pages.length,fullRangeConstructed:true,lastSlotIssued:true,crossPageRollback:true,staleAfterRefundRejected:true,cancelledIssueRejected:true});
 console.log(JSON.stringify(evidence.cases.at(-1)));
}
mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(evidence,null,2)+'\n');
