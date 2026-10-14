// BCS parsers for the kix_rights_scale package objects and events. Field order
// must match sui/sources/rights_scale.move exactly.
import {bcs} from '@mysten/sui/bcs';
const bytes=bcs.vector(bcs.u8());
const offer=bcs.struct('Offer',{recipient:bcs.Address,amount:bcs.u64(),expires_ms:bcs.u64(),version:bcs.u64(),terms:bytes});
const admission=bcs.struct('Admission',{gate:bcs.Address,expires_ms:bcs.u64(),version:bcs.u64(),request:bytes});
export const ShowControl=bcs.struct('ShowControl',{id:bcs.Address,issuer:bcs.Address,profile_version:bcs.u64(),open:bcs.bool(),
  sealed:bcs.bool(),cancel_generation:bcs.u64(),verifier:bcs.Address,gates:bcs.vector(bcs.Address),
  payment_attesters:bcs.vector(bcs.Address),resale_cap:bcs.u64(),organizer_bps:bcs.u64(),platform_bps:bcs.u64(),
  page_size:bcs.u64(),seated_capacity:bcs.u64(),ga_capacity:bcs.u64(),seated_pages:bcs.u64(),page_count:bcs.u64(),
  shard_count:bcs.u64(),claimed_pages:bcs.u64(),claimed_shards:bcs.u64(),claim_sequence:bcs.u64(),domain:bcs.u256()});
export const InventoryPage=bcs.struct('InventoryPage',{id:bcs.Address,show:bcs.Address,index:bcs.u64(),start:bcs.u64(),end:bcs.u64(),
  mode:bcs.u8(),generations:bcs.vector(bcs.u64()),occupied:bcs.vector(bcs.bool()),issuances:bcs.u64(),free:bcs.u64(),
  reserved:bcs.u64(),issued:bcs.u64(),retired:bcs.u64(),delegated_to:bcs.option(bcs.Address)});
// A Table serializes as its UID only; dynamic fields carry the entries.
export const PaymentRefShard=bcs.struct('PaymentRefShard',{id:bcs.Address,show:bcs.Address,index:bcs.u64(),refs:bcs.Address});
export const Ticket=bcs.struct('Ticket',{id:bcs.Address,show:bcs.Address,slot:bcs.u64(),generation:bcs.u64(),holder:bcs.Address,
  version:bcs.u64(),state:bcs.u8(),offer:bcs.option(offer),admission:bcs.option(admission),last_payment:bytes,
  last_amount:bcs.u64(),last_payer:bcs.Address});
export const IssuancePayment=bcs.struct('IssuancePayment',{id:bcs.Address,show:bcs.Address,slot:bcs.u64(),
  expected_generation:bcs.u64(),buyer:bcs.Address,amount:bcs.u64(),payment_ref:bytes});
export const PaymentEvidence=bcs.struct('PaymentEvidence',{id:bcs.Address,show:bcs.Address,ticket:bcs.Address,version:bcs.u64(),
  buyer:bcs.Address,seller:bcs.Address,amount:bcs.u64(),terms:bytes,payment_ref:bytes});
export const ShowControlCreated=bcs.struct('ShowControlCreated',{show:bcs.Address,issuer:bcs.Address,profile_version:bcs.u64(),
  page_count:bcs.u64(),shard_count:bcs.u64()});
export const PageClaimed=bcs.struct('PageClaimed',{show:bcs.Address,index:bcs.u64(),page:bcs.Address,claim_sequence:bcs.u64()});
export const ShardClaimed=bcs.struct('ShardClaimed',{show:bcs.Address,index:bcs.u64(),shard:bcs.Address,claim_sequence:bcs.u64()});
export const Issuance=bcs.struct('Issuance',{show:bcs.Address,ticket:bcs.Address,slot:bcs.u64(),generation:bcs.u64(),
  holder:bcs.Address,kind:bcs.u8(),amount:bcs.u64(),payment_ref:bytes});
export const Clock=bcs.struct('Clock',{id:bcs.Address,timestamp_ms:bcs.u64()});

// RS-2: the private path. A Table serializes as its UID and a length; entries are dynamic fields.
const table=bcs.struct('Table',{id:bcs.Address,size:bcs.u64()});
export const NoteTree=bcs.struct('NoteTree',{id:bcs.Address,show:bcs.Address,depth:bcs.u64(),history_k:bcs.u64(),leaf_count:bcs.u64(),
  frontier:bcs.vector(bcs.u256()),zeros:bcs.vector(bcs.u256()),root:bcs.u256(),roots:bcs.vector(bcs.u256()),head:bcs.u64()});
export const RevocationState=bcs.struct('RevocationState',{id:bcs.Address,show:bcs.Address,depth:bcs.u64(),root:bcs.u256(),revocations:bcs.u64()});
export const NullifierShard=bcs.struct('NullifierShard',{id:bcs.Address,show:bcs.Address,index:bcs.u64(),spent:table});
export const ChallengeShard=bcs.struct('ChallengeShard',{id:bcs.Address,show:bcs.Address,index:bcs.u64(),used:table});
export const ZkClaimed=bcs.struct('ZkClaimed',{show:bcs.Address,domain:bcs.u256(),note_tree:bcs.Address,revocation:bcs.Address,
  nullifier_shards:bcs.vector(bcs.Address),challenge_shards:bcs.vector(bcs.Address),depth:bcs.u64(),history_k:bcs.u64(),claim_sequence:bcs.u64()});
export const NoteAdded=bcs.struct('NoteAdded',{show:bcs.Address,index:bcs.u64(),commitment:bcs.u256(),root:bcs.u256()});
export const RevocationLeaf=bcs.struct('RevocationLeaf',{show:bcs.Address,slot:bcs.u64(),generation:bcs.u64(),root:bcs.u256()});
export const PrivateAdmission=bcs.struct('PrivateAdmission',{show:bcs.Address,nullifier:bcs.u256(),gate:bcs.Address,challenge:bcs.u256(),note_root:bcs.u256()});
export const Change=bcs.struct('Change',{show:bcs.Address,ticket:bcs.Address,version:bcs.u64(),state:bcs.u8(),holder:bcs.Address,kind:bcs.u8()});
export const Verifier=bcs.struct('Verifier',{id:bcs.Address,circuit_manifest_hash:bytes,mint_vk:bytes,spend_vk:bytes});
