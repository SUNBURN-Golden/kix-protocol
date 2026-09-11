import {bcs} from '@mysten/sui/bcs';
const bytes=bcs.vector(bcs.u8());
const offer=bcs.struct('Offer',{recipient:bcs.Address,amount:bcs.u64(),expires_ms:bcs.u64(),version:bcs.u64(),terms:bytes});
const admission=bcs.struct('Admission',{gate:bcs.Address,expires_ms:bcs.u64(),version:bcs.u64(),request:bytes});
export const Ticket=bcs.struct('Ticket',{id:bcs.Address,show:bcs.Address,slot:bcs.u64(),generation:bcs.u64(),holder:bcs.Address,
  version:bcs.u64(),state:bcs.u8(),offer:bcs.option(offer),admission:bcs.option(admission),last_payment:bytes,last_amount:bcs.u64(),last_payer:bcs.Address});
export const Show=bcs.struct('Show',{id:bcs.Address,issuer:bcs.Address,open:bcs.bool(),capacity:bcs.u64(),issued:bcs.u64(),
  generations:bcs.vector(bcs.u64()),occupied:bcs.vector(bcs.bool()),gates:bcs.vector(bcs.Address),payment_attesters:bcs.vector(bcs.Address),
  payment_refs:bcs.vector(bytes),resale_cap:bcs.u64(),organizer_bps:bcs.u64(),platform_bps:bcs.u64(),verifier:bcs.Address,domain:bcs.u256(),
  notes:bcs.vector(bcs.u256()),nullifiers:bcs.vector(bcs.u256()),spent_challenges:bcs.vector(bcs.u256())});
export const Change=bcs.struct('Change',{show:bcs.Address,ticket:bcs.Address,version:bcs.u64(),state:bcs.u8(),holder:bcs.Address,kind:bcs.u8()});
export const Clock=bcs.struct('Clock',{id:bcs.Address,timestamp_ms:bcs.u64()});
export const Verifier=bcs.struct('Verifier',{id:bcs.Address,circuit_manifest_hash:bytes,mint_vk:bytes,spend_vk:bytes});
