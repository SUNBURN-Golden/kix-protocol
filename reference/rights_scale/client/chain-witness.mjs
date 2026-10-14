// RR-4: rebuild the public tree data a witness needs from CHAIN data alone, with no local
// cache and no indexer service. The note tree keeps only a frontier, so its leaves are read
// from `NoteAdded` events and the revocation leaves from `RevocationLeaf` events. Two event
// sources are implemented and must agree (blueprint 5.6 item 4):
//   1. the node's own JSON-RPC event query (`suix_queryEvents`),
//   2. a scan of every checkpoint's transactions through the node's gRPC ledger service.
// Whichever source is used, the rebuilt roots are checked against the roots stored on chain,
// so a source that omits or invents an event cannot produce an accepted witness.
import {SuiJsonRpcClient} from '@mysten/sui/jsonRpc';
import {NoteAdded,RevocationLeaf,NoteTree,RevocationState} from './types.mjs';
import {exact} from './chain-kit.mjs';
import {poseidon,noteTreeOf,revocationTreeOf} from './private-scale.mjs';
import {DEPTH} from './profile-constants.mjs';

const typeOf=(packageId,name)=>packageId+'::rights_scale::'+name;
const same=(a,b)=>BigInt(a)===BigInt(b);

/** Source 1: JSON-RPC `suix_queryEvents` by Move event type, oldest first, paged. */
export function jsonRpcEventSource(endpoint) {
  const client=new SuiJsonRpcClient({url:endpoint,network:'localnet'});
  return {
    name:'jsonrpc-queryEvents',
    async events(packageId,name) {
      const out=[];let cursor=null;
      do{
        const page=await client.queryEvents({query:{MoveEventType:typeOf(packageId,name)},cursor,limit:50,order:'ascending'});
        for(const e of page.data)out.push({bcs:Buffer.from(e.bcs,'base64'),digest:e.id.txDigest,seq:Number(e.id.eventSeq)});
        cursor=page.hasNextPage?page.nextCursor:null;
      }while(cursor);
      return out;
    },
  };
}

/**
 * Source 2: every checkpoint's transactions via gRPC; no event index is consulted. The scan is
 * incremental: checkpoints already read are kept, so each event type and each later call only
 * reads the checkpoints that are new.
 */
export function checkpointEventSource(rpc) {
  const seen=[];        // {type, bcs, digest, seq} of every event read so far, in chain order
  let next=0;           // first checkpoint not read yet
  const samePackage=(type,packageId)=>{
    const [pkg,mod]=type.split('::');
    return mod==='rights_scale' && BigInt(pkg)===BigInt(packageId);
  };
  return {
    name:'grpc-checkpoint-scan',
    async events(packageId,name) {
      const info=await rpc.ledgerService.getServiceInfo({});
      const latest=Number(info.response.checkpointHeight);
      for(;next<=latest;next++) {
        const {response}=await rpc.ledgerService.getCheckpoint({checkpointId:{oneofKind:'sequenceNumber',sequenceNumber:BigInt(next)},
          readMask:{paths:['transactions.digest','transactions.events']}});
        for(const tx of response.checkpoint?.transactions??[]) {
          let seq=0;
          for(const e of tx.events?.events??[]) {
            seen.push({type:e.eventType,bcs:Buffer.from(e.contents?.value??[]),digest:tx.digest,seq});
            seq++;
          }
        }
      }
      return seen.filter(e=>samePackage(e.type,packageId) && e.type.endsWith('::rights_scale::'+name));
    },
  };
}

/**
 * Public tree data of one show, rebuilt from `source`. Throws unless the rebuilt note root is
 * the root stored in the NoteTree object (or one of its recent roots, for `atCount` witnesses)
 * and the rebuilt revocation root is the one stored in the RevocationState object.
 */
export async function rebuildTreeView({source,packageId,controlId,treeId,revocationId,domain,getFields}) {
  const H=await poseidon();
  const added=(await source.events(packageId,'NoteAdded')).map(e=>exact(NoteAdded.parse(e.bcs))).filter(e=>e.show===controlId);
  added.sort((a,b)=>Number(a.index)-Number(b.index));
  added.forEach((e,i)=>{if(Number(e.index)!==i)throw Error('NOTE_EVENT_GAP:'+i);});
  const noteLeaves=added.map(e=>BigInt(e.commitment));
  const revokedEvents=(await source.events(packageId,'RevocationLeaf')).map(e=>exact(RevocationLeaf.parse(e.bcs))).filter(e=>e.show===controlId);
  const revoked=new Map();
  for(const e of revokedEvents)revoked.set(Number(e.slot),BigInt(e.generation)>(revoked.get(Number(e.slot))??0n)?BigInt(e.generation):revoked.get(Number(e.slot)));
  const tree=await getFields(treeId,NoteTree),rev=await getFields(revocationId,RevocationState);
  if(!same(noteTreeOf(H,noteLeaves,DEPTH).root,tree.root)||noteLeaves.length!==Number(tree.leaf_count))throw Error('REBUILT_NOTE_ROOT_MISMATCH:'+source.name);
  // Every event root is a historical root of the same append-only tree.
  added.forEach((e,i)=>{if(!same(noteTreeOf(H,noteLeaves.slice(0,i+1),DEPTH).root,e.root))throw Error('NOTE_EVENT_ROOT_MISMATCH:'+i);});
  if(!same(revocationTreeOf(H,revoked,DEPTH).root,rev.root)||revokedEvents.length!==Number(rev.revocations))throw Error('REBUILT_REVOCATION_ROOT_MISMATCH:'+source.name);
  return {domain,noteLeaves,revoked,source:source.name,noteEvents:added.length,revocationEvents:revokedEvents.length};
}
