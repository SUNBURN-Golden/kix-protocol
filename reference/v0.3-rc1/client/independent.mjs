import {SuiGrpcClient} from '@mysten/sui/grpc';
import {Transaction} from '@mysten/sui/transactions';
import {Ed25519Keypair} from '@mysten/sui/keypairs/ed25519';
import {Ticket,Show,Clock} from './types.mjs';
import {durableJSON,readJSON,seal,unseal} from './backup.mjs';
import {randomBytes} from 'node:crypto';
import {join} from 'node:path';

export class IndependentClient {
  constructor({endpoint,network='localnet',expectedChain,packageId,keypair,journal}) {
    this.rpc=new SuiGrpcClient({network,baseUrl:endpoint});
    Object.assign(this,{expectedChain,packageId,keypair,journal});
  }
  async chain() {
    const result=await this.rpc.getChainIdentifier();
    const chain=typeof result==='string'?result:result.chainIdentifier;
    if(!chain || this.expectedChain && chain!==this.expectedChain)throw Error('CHAIN_PIN_MISMATCH');
    return chain;
  }
  async object(id,type,parser) {
    const {object}=await this.rpc.getObject({objectId:id,include:{content:true,previousTransaction:true}});
    if(object.type!==this.packageId+'::rights::'+type)throw Error('OBJECT_TYPE_MISMATCH');
    return {object,fields:parser.parse(object.content)};
  }
  async right(showId,ticketId) {
    await this.chain();
    const [s,t]=await Promise.all([this.object(showId,'Show',Show),this.object(ticketId,'Ticket',Ticket)]);
    if(t.fields.show!==showId)throw Error('RIGHT_SHOW_MISMATCH');
    const valid=s.fields.open && t.fields.state===0 && t.fields.generation===s.fields.generations[Number(t.fields.slot)];
    return {show:s.fields,ticket:t.fields,valid,objectVersion:t.object.version,previousTransaction:t.object.previousTransaction};
  }
  async now() {
    const {object}=await this.rpc.getObject({objectId:'0x6',include:{content:true}});
    return BigInt(Clock.parse(object.content).timestamp_ms);
  }
  async submit(tx,label) {
    await this.chain(); tx.setSender(this.keypair.toSuiAddress()); tx.setGasBudget(100000000);
    const bytes=await tx.build({client:this.rpc});
    const signed=await this.keypair.signTransaction(bytes);
    const digest=await tx.getDigest({client:this.rpc});
    const path=join(this.journal,label+'-'+digest+'.json');
    const record={chain:this.expectedChain,packageId:this.packageId,digest,bytes:Buffer.from(bytes).toString('base64'),
      signatures:[signed.signature],state:'SIGNED_NOT_CONFIRMED'};
    await durableJSON(path,record);
    let result;
    try {
      result=await this.rpc.executeTransaction({transaction:bytes,signatures:record.signatures,include:{effects:true,events:true,objectTypes:true}});
      await this.rpc.waitForTransaction({result,timeout:20000});
    } catch (error) {
      await durableJSON(path,{...record,state:'OUTCOME_UNKNOWN',error:String(error)}); throw error;
    }
    const executed=result.Transaction??result.FailedTransaction;
    if(!executed)throw Error('UNRECOGNIZED_EXECUTION_RESULT');
    await durableJSON(path,{...record,state:executed.status.success?'EXECUTED_SUCCESS':'EXECUTED_FAILURE',result});
    if(!executed.status.success)throw Error('CHAIN_EXECUTION_FAILED:'+JSON.stringify(executed.status));
    return executed;
  }
  call(fn,args){const tx=new Transaction();tx.moveCall({target:this.packageId+'::rights::'+fn,arguments:args(tx)});return this.submit(tx,fn);}
  offer(show,ticket,version,recipient,amount,expires) {
    return this.call('offer',t=>[t.object(show),t.object(ticket),t.pure.u64(version),t.pure.address(recipient),t.pure.u64(amount),t.pure.u64(expires),t.object('0x6')]);
  }
  acceptGift(show,ticket){return this.call('accept_gift',t=>[t.object(show),t.object(ticket),t.object('0x6')]);}
  authorize(show,ticket,version,gate,request,expires) {
    return this.call('authorize_admission',t=>[t.object(show),t.object(ticket),t.pure.u64(version),t.pure.address(gate),t.pure.vector('u8',request),t.pure.u64(expires),t.object('0x6')]);
  }
  consume(show,ticket,version,request) {
    return this.call('consume',t=>[t.object(show),t.object(ticket),t.pure.u64(version),t.pure.vector('u8',request),t.object('0x6')]);
  }
  async backup(path,passphrase,showId,ticketId,extra={}) {
    const current=await this.right(showId,ticketId);
    if(current.ticket.holder!==this.keypair.toSuiAddress())throw Error('NOT_BACKUP_HOLDER');
    const payload={format:'kix-holder-v1',chain:await this.chain(),packageId:this.packageId,showId,ticketId,
      secretKey:this.keypair.getSecretKey(),rightVersion:current.ticket.version,extra};
    await durableJSON(path,seal(payload,passphrase));
    return {path,holder:this.keypair.toSuiAddress(),rightVersion:current.ticket.version};
  }
  static async restore(path,passphrase,{endpoint,journal,network='localnet'}) {
    const b=unseal(await readJSON(path),passphrase);
    if(b.format!=='kix-holder-v1')throw Error('HOLDER_BACKUP_FORMAT');
    const client=new IndependentClient({endpoint,network,expectedChain:b.chain,packageId:b.packageId,
      keypair:Ed25519Keypair.fromSecretKey(b.secretKey),journal});
    const current=await client.right(b.showId,b.ticketId);
    if(current.ticket.holder!==client.keypair.toSuiAddress())throw Error('OLD_HOLDER_BACKUP');
    return {client,backup:b,current};
  }
  async recoverSubmission(path,{resubmitExactBytes=false}={}) {
    await this.chain();const saved=await readJSON(path);
    if(saved.chain!==this.expectedChain || saved.packageId!==this.packageId)throw Error('SIGNED_TX_PIN_MISMATCH');
    try {
      const result=await this.rpc.getTransaction({digest:saved.digest,include:{effects:true,events:true}});
      const tx=result.Transaction??result.FailedTransaction;
      return {state:tx.status.success?'EXECUTED_SUCCESS':'EXECUTED_FAILURE',result};
    } catch(error) {
      if(!resubmitExactBytes)return {state:'OUTCOME_UNKNOWN',digest:saved.digest};
      const result=await this.rpc.executeTransaction({transaction:Buffer.from(saved.bytes,'base64'),signatures:saved.signatures,include:{effects:true,events:true}});
      await this.rpc.waitForTransaction({result,timeout:20000});return {result};
    }
  }
}
export const challengeBytes=()=>Array.from(randomBytes(32));
